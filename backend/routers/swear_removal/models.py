"""
Pydantic models for swear removal API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from fastapi import Form


class SwearRemovalParams(BaseModel):
    """Parameters for swear removal processing."""
    
    beep: bool = Field(default=False, description="Use beep instead of mute")
    beep_hertz: int = Field(default=1000, description="Beep frequency in Hz")
    pad_milliseconds_pre: int = Field(default=0, description="Padding before censored word (ms)")
    pad_milliseconds_post: int = Field(default=0, description="Padding after censored word (ms)")
    output_format: str = Field(default="MATCH", description="Output audio format")
    channels: int = Field(default=2, description="Number of audio channels")
    sample_rate: int = Field(default=48000, description="Audio sample rate")
    use_custom_list: bool = Field(default=False, description="Use custom swear list")
    custom_list_id: Optional[str] = Field(default=None, description="ID of custom swear list")
    reuse_transcript: bool = Field(default=True, description="Reuse existing transcript if available")
    
    @classmethod
    def as_form(
        cls,
        beep: bool = Form(False),
        beep_hertz: int = Form(1000),
        pad_milliseconds_pre: int = Form(0),
        pad_milliseconds_post: int = Form(0),
        output_format: str = Form("MATCH"),
        channels: int = Form(2),
        sample_rate: int = Form(48000),
        use_custom_list: bool = Form(False),
        custom_list_id: Optional[str] = Form(None),
        reuse_transcript: bool = Form(True),
    ):
        """Create parameters from form data."""
        return cls(
            beep=beep,
            beep_hertz=beep_hertz,
            pad_milliseconds_pre=pad_milliseconds_pre,
            pad_milliseconds_post=pad_milliseconds_post,
            output_format=output_format,
            channels=channels,
            sample_rate=sample_rate,
            use_custom_list=use_custom_list,
            custom_list_id=custom_list_id,
            reuse_transcript=reuse_transcript,
        )


class CensoredWord(BaseModel):
    """Information about a censored word."""
    
    word: str = Field(..., description="The censored word")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    confidence: float = Field(..., description="Transcription confidence")


class SwearRemovalResult(BaseModel):
    """Result of swear removal processing."""
    
    audio_hash: str = Field(..., description="Hash of output audio file")
    transcript_hash: Optional[str] = Field(None, description="Hash of transcript file")
    statistics_hash: Optional[str] = Field(None, description="Hash of statistics file")
    censored_count: int = Field(..., description="Number of words censored")
    total_words: int = Field(..., description="Total words in transcription")
    censored_words: List[CensoredWord] = Field(default_factory=list, description="List of censored words")
    duration_cleaned: float = Field(..., description="Total audio duration in seconds")
    transcript_reused: bool = Field(default=False, description="Whether existing transcript was reused")


class SwearListInfo(BaseModel):
    """Information about a swear list."""
    
    list_id: str = Field(..., description="Unique identifier for the list")
    name: str = Field(..., description="Display name")
    word_count: int = Field(..., description="Number of words in list")
    is_default: bool = Field(..., description="Whether this is the default list")


class SwearListUploadResponse(BaseModel):
    """Response after uploading a swear list."""
    
    list_id: str = Field(..., description="ID assigned to the uploaded list")
    word_count: int = Field(..., description="Number of words loaded")
    message: str = Field(..., description="Status message")
