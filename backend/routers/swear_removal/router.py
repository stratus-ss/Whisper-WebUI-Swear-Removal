
import functools
import os
import glob
import numpy as np
import soundfile as sf
from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, HTTPException, status
from typing import List, Optional, Tuple, Dict
from datetime import datetime
import gradio as gr

from backend.common.audio import read_audio
from backend.common.models import QueueResponse
from backend.common.compresser import get_file_hash
from backend.db.task.models import TaskStatus, TaskType, ResultType
from backend.db.task.dao import add_task_to_db, update_task_status_in_db
from backend.routers.transcription.router import get_pipeline
from modules.swear_removal.swear_manager import SwearListManager
from modules.swear_removal.audio_cleaner import AudioCleaner
from modules.swear_removal.statistics import CensorshipStatistics
from modules.swear_removal.swear_service import SwearRemovalService
from modules.utils.paths import (
    SWEAR_REMOVAL_AUDIO_OUTPUT_DIR,
    SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR,
    BACKEND_CACHE_DIR
)
from modules.utils.logger import get_logger
from .models import (
    SwearRemovalParams,
    SwearRemovalResult,
    CensoredWord,
    SwearListInfo,
    SwearListUploadResponse
)

logger = get_logger()

swear_removal_router = APIRouter(prefix="/swear-removal", tags=["Swear Removal"])


@functools.lru_cache
def get_swear_manager() -> SwearListManager:
    """Get or create the SwearListManager singleton."""
    return SwearListManager()


@functools.lru_cache
def get_audio_cleaner() -> AudioCleaner:
    """Get or create the AudioCleaner singleton."""
    return AudioCleaner()


def _update_task_progress(identifier: str, progress: float, status_val: TaskStatus = TaskStatus.IN_PROGRESS) -> None:
    """
    Update task status in database.
    
    Args:
        identifier: Task identifier
        progress: Progress value (0.0 to 1.0)
        status_val: Task status
    """
    update_task_status_in_db(
        identifier=identifier,
        update_data={
            "uuid": identifier,
            "status": status_val,
            "progress": progress,
            "updated_at": datetime.utcnow()
        }
    )


def _save_temp_audio(audio: np.ndarray, base_name: str, timestamp: str, sample_rate: int) -> str:
    """
    Save audio to temporary file.
    
    Args:
        audio: Audio data
        base_name: Base name for file
        timestamp: Timestamp string
        sample_rate: Audio sample rate
        
    Returns:
        Path to temporary file
    """
    temp_path = os.path.join(BACKEND_CACHE_DIR, f"{base_name}_temp_{timestamp}.wav")
    sf.write(temp_path, audio, sample_rate)
    return temp_path


def run_swear_removal(
    audio: np.ndarray,
    file_name: str,
    params: SwearRemovalParams,
    identifier: str,
) -> SwearRemovalResult:
    """
    Run swear removal processing in background.
    
    Args:
        audio: Audio data as numpy array
        file_name: Original filename
        params: Swear removal parameters
        identifier: Task identifier
        
    Returns:
        SwearRemovalResult with file hashes and statistics
    """
    _update_task_progress(identifier, 0.1)
    start_time = datetime.utcnow()
    
    try:
        # Prepare paths and names
        base_name = os.path.splitext(file_name)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get or create transcript
        word_list, transcript_reused = _get_or_create_transcript(
            audio, base_name, params.reuse_transcript, identifier
        )
        
        _update_task_progress(identifier, 0.6)
        
        # Load swear list
        swears_dict = _load_swear_list(params)
        
        # Save temp audio and get paths
        temp_input_path = _save_temp_audio(audio, base_name, timestamp, params.sample_rate)
        output_filename = _get_output_filename(base_name, timestamp, params.output_format, file_name)
        output_path = os.path.join(SWEAR_REMOVAL_AUDIO_OUTPUT_DIR, output_filename)
        
        transcript_path = os.path.join(
            SWEAR_REMOVAL_TRANSCRIPT_OUTPUT_DIR,
            f"{base_name}_transcript_{timestamp}.json"
        )
        
        _update_task_progress(identifier, 0.7)
        
        # Clean audio
        cleaned_path, censored_words = _clean_audio(
            temp_input_path, output_path, word_list, swears_dict,
            params, transcript_path if not transcript_reused else None
        )
        
        # Clean up temp file
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        
        _update_task_progress(identifier, 0.9)
        
        # Generate statistics and save files
        audio_duration = len(audio) / params.sample_rate
        result = _create_result(
            word_list, censored_words, audio_duration,
            base_name, timestamp, output_path, transcript_reused
        )
        
        elapsed_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Update task with completion
        update_task_status_in_db(
            identifier=identifier,
            update_data={
                "uuid": identifier,
                "status": TaskStatus.COMPLETED,
                "result": result.model_dump(),
                "result_type": ResultType.FILEPATH,
                "updated_at": datetime.utcnow(),
                "duration": elapsed_time,
                "progress": 1.0,
            }
        )
        
        logger.info(f"Swear removal completed in {elapsed_time:.2f}s")
        return result
        
    except Exception as e:
        logger.error(f"Swear removal failed: {str(e)}", exc_info=True)
        
        update_task_status_in_db(
            identifier=identifier,
            update_data={
                "uuid": identifier,
                "status": TaskStatus.FAILED,
                "error": str(e),
                "updated_at": datetime.utcnow()
            }
        )
        
        raise


def _load_swear_list(params: SwearRemovalParams) -> Dict[str, str]:
    """
    Load swear list based on parameters.
    
    Args:
        params: Swear removal parameters
        
    Returns:
        Dictionary of swear words
    """
    swear_manager = get_swear_manager()
    
    if params.use_custom_list and params.custom_list_id:
        swears_dict = swear_manager.get_swears_dict(params.custom_list_id)
        logger.info(f"Using custom swear list: {params.custom_list_id}")
    else:
        swears_dict = swear_manager.load_default_list()
        logger.info("Using default swear list")
    
    return swears_dict


def _clean_audio(
    temp_input_path: str,
    output_path: str,
    word_list: List[Dict],
    swears_dict: Dict[str, str],
    params: SwearRemovalParams,
    transcript_path: Optional[str]
) -> Tuple[str, List[Dict]]:
    """
    Clean audio file.
    
    Args:
        temp_input_path: Path to temporary input file
        output_path: Path for output file
        word_list: List of words with timing
        swears_dict: Dictionary of swear words
        params: Swear removal parameters
        transcript_path: Path to save transcript (None if reused)
        
    Returns:
        Tuple of (cleaned_path, censored_words)
    """
    audio_cleaner = get_audio_cleaner()
    cleaned_path, censored_words = audio_cleaner.clean_audio(
        input_path=temp_input_path,
        output_path=output_path,
        word_list=word_list,
        swears_dict=swears_dict,
        beep=params.beep,
        beep_hertz=params.beep_hertz,
        pad_ms_pre=params.pad_milliseconds_pre,
        pad_ms_post=params.pad_milliseconds_post,
        output_format=params.output_format,
        channels=params.channels,
        sample_rate=params.sample_rate,
        transcript_path=transcript_path,
    )
    
    logger.info(f"Audio cleaning complete: {len(censored_words)} words censored")
    return cleaned_path, censored_words


def _create_result(
    word_list: List[Dict],
    censored_words: List[Dict],
    audio_duration: float,
    base_name: str,
    timestamp: str,
    output_path: str,
    transcript_reused: bool
) -> SwearRemovalResult:
    """
    Create result object with statistics.
    
    Args:
        word_list: List of all words
        censored_words: List of censored words
        audio_duration: Duration of audio in seconds
        base_name: Base name of file
        timestamp: Timestamp string
        output_path: Path to output audio file
        transcript_reused: Whether transcript was reused
        
    Returns:
        SwearRemovalResult object
    """
    stats_generator = CensorshipStatistics()
    analysis = stats_generator.analyze_results(word_list, censored_words, audio_duration)
    
    transcript_path, stats_path = _save_statistics_files(
        base_name, timestamp, word_list, censored_words, analysis
    )
    
    audio_hash = get_file_hash(output_path)
    transcript_hash = get_file_hash(transcript_path)
    stats_hash = get_file_hash(stats_path)
    
    return SwearRemovalResult(
        audio_hash=audio_hash,
        transcript_hash=transcript_hash,
        statistics_hash=stats_hash,
        censored_count=len(censored_words),
        total_words=len(word_list),
        censored_words=[
            CensoredWord(
                word=w.get('original_word', w.get('word', '')),
                start=w.get('start', 0),
                end=w.get('end', 0),
                confidence=w.get('conf', 1.0)
            )
            for w in censored_words
        ],
        duration_cleaned=audio_duration,
        transcript_reused=transcript_reused
    )


@swear_removal_router.post(
    "/",
    response_model=QueueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Remove swear words from audio",
    description="Process an audio file to remove profanity by muting or beeping."
)
async def remove_swears(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio or video file to clean"),
    params: SwearRemovalParams = Depends(SwearRemovalParams.as_form)
) -> QueueResponse:
    """
    Remove swear words from uploaded audio file.
    """
    audio, info = await read_audio(file=file)
    
    identifier = add_task_to_db(
        status=TaskStatus.QUEUED,
        file_name=file.filename,
        audio_duration=info.duration if info else None,
        task_type=TaskType.SWEAR_REMOVAL,
        task_params=params.model_dump(),
    )
    
    background_tasks.add_task(
        run_swear_removal,
        audio=audio,
        file_name=file.filename,
        params=params,
        identifier=identifier
    )
    
    return QueueResponse(
        identifier=identifier,
        status=TaskStatus.QUEUED,
        message="Swear removal task has been queued"
    )


@swear_removal_router.get(
    "/swear-lists",
    response_model=List[SwearListInfo],
    summary="List available swear lists",
    description="Get information about available swear word lists."
)
async def list_swear_lists() -> List[SwearListInfo]:
    """
    List all available swear lists.
    """
    swear_manager = get_swear_manager()
    lists = []
    
    # Add default list
    default_dict = swear_manager.load_default_list()
    lists.append(SwearListInfo(
        list_id="default",
        name="Default Swear List",
        word_count=len(default_dict),
        is_default=True
    ))
    
    for list_id in swear_manager.custom_lists.keys():
        try:
            custom_dict = swear_manager.get_swears_dict(list_id)
            lists.append(SwearListInfo(
                list_id=list_id,
                name=f"Custom List: {list_id}",
                word_count=len(custom_dict),
                is_default=False
            ))
        except Exception as e:
            logger.warning(f"Could not load custom list {list_id}: {e}")
    
    return lists


@swear_removal_router.post(
    "/swear-lists/upload",
    response_model=SwearListUploadResponse,
    summary="Upload custom swear list",
    description="Upload a custom swear word list (text or JSON format)."
)
async def upload_swear_list(
    file: UploadFile = File(..., description="Swear list file (txt or json)"),
    list_id: str = "custom"
) -> SwearListUploadResponse:
    """
    Upload a custom swear list.
    """
    # Save uploaded file temporarily
    temp_path = os.path.join(BACKEND_CACHE_DIR, f"swear_list_{list_id}_{file.filename}")
    
    try:
        with open(temp_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        # Load the list to validate it
        swear_manager = get_swear_manager()
        swears_dict = swear_manager.load_custom_list(temp_path, list_id)
        
        return SwearListUploadResponse(
            list_id=list_id,
            word_count=len(swears_dict),
            message=f"Successfully uploaded swear list '{list_id}' with {len(swears_dict)} words"
        )
        
    except Exception as e:
        logger.error(f"Failed to upload swear list: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process swear list: {str(e)}"
        )


@swear_removal_router.get(
    "/swear-lists/{list_id}",
    response_model=List[str],
    summary="Get swear list contents",
    description="Retrieve the contents of a specific swear list."
)
async def get_swear_list(list_id: str) -> List[str]:
    """
    Get the contents of a swear list.
    """
    try:
        swear_manager = get_swear_manager()
        swears_dict = swear_manager.get_swears_dict(list_id)
        
        # Return just the words (keys)
        return list(swears_dict.keys())
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get swear list {list_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve swear list: {str(e)}"
        )
