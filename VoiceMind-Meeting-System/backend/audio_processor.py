"""
Audio processing utilities
"""
import logging
import os
from config import UPLOAD_FOLDER

logger = logging.getLogger(__name__)

def save_audio_chunk_to_file(meeting_id: str, chunk_number: int, audio_data: bytes):
    """
    Save audio chunk to file system
    
    Args:
        meeting_id: Meeting identifier
        chunk_number: Chunk sequence number
        audio_data: Raw audio bytes
    
    Returns:
        str: File path
    """
    try:
        meeting_folder = os.path.join(UPLOAD_FOLDER, meeting_id)
        os.makedirs(meeting_folder, exist_ok=True)
        
        filename = f"chunk_{chunk_number:04d}.wav"
        filepath = os.path.join(meeting_folder, filename)
        
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        logger.info(f"Saved audio chunk to: {filepath}")
        return filepath
    
    except Exception as e:
        logger.error(f"Error saving audio chunk: {e}")
        return None

def cleanup_old_files(meeting_id: str):
    """Delete temporary audio files after processing"""
    try:
        meeting_folder = os.path.join(UPLOAD_FOLDER, meeting_id)
        if os.path.exists(meeting_folder):
            for file in os.listdir(meeting_folder):
                os.remove(os.path.join(meeting_folder, file))
            os.rmdir(meeting_folder)
            logger.info(f"Cleaned up files for meeting: {meeting_id}")
    except Exception as e:
        logger.error(f"Error cleaning up files: {e}")
