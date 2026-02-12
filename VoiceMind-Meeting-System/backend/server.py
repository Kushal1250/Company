"""
FastAPI server for VoiceMind Meeting System
"""
from fastapi import FastAPI, File, UploadFile, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import uvicorn

# Import local modules
from database import (
    init_database, close_database, create_meeting, get_meeting,
    update_meeting_status, save_audio_chunk, get_all_chunks,
    save_qa_interaction, list_all_meetings, log_system_event
)
from transcription_service import transcribe_audio
from qa_service import answer_question, generate_summary, extract_agenda, extract_action_items
from audio_processor import save_audio_chunk_to_file
from config import SERVER_HOST, SERVER_PORT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="VoiceMind Meeting API",
    description="AI-powered meeting recording and analysis system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Startup and Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    logger.info("Starting VoiceMind API server...")
    init_database()
    log_system_event("INFO", "Server started")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    logger.info("Shutting down VoiceMind API server...")
    log_system_event("INFO", "Server stopped")
    close_database()

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "VoiceMind Meeting API",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/start_meeting")
async def start_meeting(meeting_id: str, title: str = None, language: str = "auto"):
    """
    Start a new meeting recording session
    
    Args:
        meeting_id: Unique meeting identifier
        title: Meeting title (optional)
        language: Language code or 'auto' for detection
    """
    try:
        logger.info(f"Starting meeting: {meeting_id}")
        
        # Check if meeting already exists
        existing = get_meeting(meeting_id)
        if existing:
            raise HTTPException(status_code=400, detail="Meeting ID already exists")
        
        # Create meeting record
        create_meeting(meeting_id, title, language)
        log_system_event("INFO", f"Meeting started: {title or meeting_id}", meeting_id)
        
        return {
            "status": "success",
            "meeting_id": meeting_id,
            "message": "Meeting recording started"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting meeting: {e}")
        log_system_event("ERROR", f"Failed to start meeting: {str(e)}", meeting_id)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload_audio")
async def upload_audio(
    file: UploadFile = File(...),
    meeting_id: str = Header(..., alias="X-Meeting-ID"),
    chunk_number: int = Header(..., alias="X-Chunk-Number"),
    chunk_timestamp: int = Header(..., alias="X-Timestamp"),
    sample_rate: int = Header(16000, alias="X-Sample-Rate")
):
    """
    Upload audio chunk and process transcription
    
    Headers:
        X-Meeting-ID: Meeting identifier
        X-Chunk-Number: Chunk sequence number
        X-Timestamp: Chunk timestamp (milliseconds)
        X-Sample-Rate: Audio sample rate
    """
    try:
        logger.info(f"Receiving chunk {chunk_number} for meeting {meeting_id}")
        
        # Read audio data
        audio_data = await file.read()
        
        # Save to database
        save_audio_chunk(meeting_id, chunk_number, chunk_timestamp, audio_data, sample_rate)
        
        # Transcribe audio
        meeting = get_meeting(meeting_id)
        language = meeting['language'] if meeting else 'auto'
        
        transcription_result = transcribe_audio(audio_data, sample_rate, language)
        transcript_text = transcription_result.get('text', '')
        
        # Update chunk with transcript
        if transcript_text:
            save_audio_chunk(meeting_id, chunk_number, chunk_timestamp, audio_data, sample_rate, transcript_text)
            logger.info(f"Chunk {chunk_number} transcribed: {transcript_text[:50]}...")
        
        return {
            "status": "success",
            "chunk_number": chunk_number,
            "transcript": transcript_text,
            "language_detected": transcription_result.get('language', 'unknown')
        }
    
    except Exception as e:
        logger.error(f"Error processing audio chunk: {e}")
        log_system_event("ERROR", f"Failed to process chunk {chunk_number}: {str(e)}", meeting_id)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/end_meeting")
async def end_meeting(meeting_id: str):
    """
    End meeting and generate final transcript and summary
    
    Args:
        meeting_id: Meeting identifier
    """
    try:
        logger.info(f"Ending meeting: {meeting_id}")
        
        # Get all chunks
        chunks = get_all_chunks(meeting_id)
        
        if not chunks:
            raise HTTPException(status_code=404, detail="No audio chunks found for this meeting")
        
        # Compile full transcript
        full_transcript = " ".join([chunk['transcript_segment'] for chunk in chunks if chunk['transcript_segment']])
        
        # Generate summary
        summary_result = generate_summary(full_transcript)
        summary = summary_result['answer']
        
        # Extract agenda
        agenda_result = extract_agenda(full_transcript)
        agenda = agenda_result['answer']
        
        # Update meeting record
        update_meeting_status(meeting_id, 'completed', full_transcript, summary)
        
        # Update agenda field separately
        from database import db
        with db.get_cursor() as cursor:
            cursor.execute("UPDATE meetings SET agenda = %s WHERE meeting_id = %s", (agenda, meeting_id))
        
        log_system_event("INFO", f"Meeting completed: {meeting_id}", meeting_id)
        
        return {
            "status": "success",
            "meeting_id": meeting_id,
            "transcript_length": len(full_transcript),
            "total_chunks": len(chunks),
            "summary": summary,
            "agenda": agenda
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending meeting: {e}")
        log_system_event("ERROR", f"Failed to end meeting: {str(e)}", meeting_id)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask_question")
async def ask_question_endpoint(meeting_id: str, question: str):
    """
    Ask a question about the meeting
    
    Args:
        meeting_id: Meeting identifier
        question: User question
    """
    try:
        logger.info(f"Q&A request for meeting {meeting_id}: {question}")
        
        # Get meeting
        meeting = get_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        transcript = meeting['full_transcript']
        if not transcript:
            raise HTTPException(status_code=400, detail="Meeting transcript not available yet")
        
        # Get answer
        result = answer_question(transcript, question)
        
        # Save Q&A interaction
        save_qa_interaction(
            meeting_id, 
            question, 
            result['answer'], 
            result['model'], 
            result['response_time']
        )
        
        return {
            "status": "success",
            "meeting_id": meeting_id,
            "question": question,
            "answer": result['answer'],
            "response_time": result['response_time']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_summary")
async def get_summary(meeting_id: str):
    """Get meeting summary"""
    try:
        meeting = get_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return {
            "status": "success",
            "meeting_id": meeting_id,
            "title": meeting['title'],
            "summary": meeting['summary'],
            "agenda": meeting['agenda'],
            "start_time": meeting['start_time'],
            "end_time": meeting['end_time'],
            "status": meeting['status']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_transcript")
async def get_transcript(meeting_id: str):
    """Get full meeting transcript"""
    try:
        chunks = get_all_chunks(meeting_id)
        
        return {
            "status": "success",
            "meeting_id": meeting_id,
            "chunks": [
                {
                    "chunk_number": c['chunk_number'],
                    "text": c['transcript_segment'],
                    "timestamp": c['chunk_timestamp']
                }
                for c in chunks
            ]
        }
    except Exception as e:
        logger.error(f"Error getting transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/list_meetings")
async def list_meetings_endpoint():
    """List all meetings"""
    try:
        meetings = list_all_meetings()
        
        return {
            "status": "success",
            "meetings": meetings
        }
    except Exception as e:
        logger.error(f"Error listing meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
        log_level="info"
    )
