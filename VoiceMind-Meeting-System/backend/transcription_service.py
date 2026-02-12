"""
Speech-to-Text transcription service using OpenAI Whisper API
"""
import openai
import logging
import io
import wave
from config import OPENAI_API_KEY, SAMPLE_RATE

openai.api_key = OPENAI_API_KEY
logger = logging.getLogger(__name__)

def transcribe_audio(audio_data: bytes, sample_rate: int = SAMPLE_RATE, language: str = None):
    """
    Transcribe audio using OpenAI Whisper API
    
    Args:
        audio_data: Raw audio bytes (PCM format)
        sample_rate: Audio sample rate
        language: Language code (e.g., 'en', 'es', 'hi') or None for auto-detect
    
    Returns:
        dict: Transcription result with text and detected language
    """
    try:
        # Convert raw PCM to WAV format
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)
        
        wav_buffer.seek(0)
        wav_buffer.name = "audio.wav"  # Whisper API requires a filename
        
        # Call Whisper API
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=wav_buffer,
            language=language if language and language != "auto" else None,
            response_format="verbose_json"
        )
        
        logger.info(f"Transcription successful. Detected language: {transcript.language}")
        
        return {
            'text': transcript.text,
            'language': transcript.language,
            'duration': transcript.duration if hasattr(transcript, 'duration') else None
        }
    
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return {
            'text': '',
            'language': 'unknown',
            'error': str(e)
        }
