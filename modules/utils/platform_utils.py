import os
import platform
from typing import Optional
from modules.utils.logger import get_logger

logger = get_logger()


class PlatformHelper:
    """Helper class for platform-specific operations."""
    
    @staticmethod
    def is_docker_environment() -> bool:
        return os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')
    
    @staticmethod
    def is_headless_environment() -> bool:
        return not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY')
    
    @staticmethod
    def ensure_directory(folder_path: str) -> None:
        """
        Create directory if it doesn't exist.
        
        Args:
            folder_path: Path to directory to ensure exists
        """
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            logger.info(f"Created directory: {folder_path}")
    
    @staticmethod
    def open_folder_in_file_manager(folder_path: str) -> Optional[str]:
        """
        Open folder in system file manager.
        
        Args:
            folder_path: Path to folder to open
            
        Returns:
            Error message if failed, None if successful
        """
        system = platform.system()
        
        try:
            if system == "Windows":
                os.system(f'start "" "{folder_path}"')
            elif system == "Darwin":  # macOS
                os.system(f'open "{folder_path}"')
            else:  # Linux
                os.system(f'xdg-open "{folder_path}"')
            
            logger.info(f"Opened folder: {folder_path}")
            return None
            
        except Exception as e:
            error_msg = f"Failed to open folder {folder_path}: {e}"
            logger.error(error_msg)
            return error_msg
    
    @staticmethod
    def open_folder(folder_path: str) -> Optional[str]:
        """
        Open folder with platform detection.
        
        Handles Docker/headless environments by returning path info for UI display.
        For GUI environments, opens the folder in the system file manager.
        
        Args:
            folder_path: Path to folder to open
        
        Returns:
            Message string for display in UI (path info for Docker/headless,
            error message if opening failed, None if opened successfully)
        """
        PlatformHelper.ensure_directory(folder_path)
        
        is_docker = PlatformHelper.is_docker_environment()
        is_headless = PlatformHelper.is_headless_environment()
        
        if is_docker or is_headless:
            env_type = "Docker container" if is_docker else "headless environment"
            message = (
                f"📁 Output Folder Location:\n\n"
                f"{folder_path}\n\n"
                f"ℹ️ Running in {env_type}\n"
                f"Files cannot be opened automatically. Please:\n"
                f"• Access via mounted volumes (Docker)\n"
                f"• Use the download buttons below\n"
                f"• Navigate to the path above manually"
            )
            logger.info(f"Output folder path ({env_type}): {folder_path}")
            print(f"Output folder: {folder_path}")
            return message
        
        # GUI environment - try to open
        error = PlatformHelper.open_folder_in_file_manager(folder_path)
        if error:
            # Return error message for UI display
            return error
        
        # Successfully opened - return path confirmation for UI
        return f"📁 Opened folder: {folder_path}"
