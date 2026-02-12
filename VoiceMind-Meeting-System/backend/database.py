"""
Database connection and ORM models using MySQL
"""
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
import logging
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    """MySQL database connection manager"""
    
    def __init__(self):
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset='utf8mb4',
                use_unicode=True
            )
            if self.connection.is_connected():
                logger.info("Successfully connected to MySQL database")
                return self.connection
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")
    
    @contextmanager
    def get_cursor(self, dictionary=True):
        """Context manager for database cursor"""
        cursor = self.connection.cursor(dictionary=dictionary)
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

# Global database instance
db = Database()

def init_database():
    """Initialize database connection"""
    db.connect()

def close_database():
    """Close database connection"""
    db.close()

# ============================================================================
# Database Helper Functions
# ============================================================================

def create_meeting(meeting_id: str, title: str = None, language: str = "auto"):
    """Create a new meeting record"""
    with db.get_cursor() as cursor:
        sql = """
            INSERT INTO meetings (meeting_id, title, status, language)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (meeting_id, title, 'recording', language))
        return cursor.lastrowid

def get_meeting(meeting_id: str):
    """Retrieve meeting by ID"""
    with db.get_cursor() as cursor:
        sql = "SELECT * FROM meetings WHERE meeting_id = %s"
        cursor.execute(sql, (meeting_id,))
        return cursor.fetchone()

def update_meeting_status(meeting_id: str, status: str, transcript: str = None, summary: str = None):
    """Update meeting status and transcript"""
    with db.get_cursor() as cursor:
        sql = """
            UPDATE meetings 
            SET status = %s, full_transcript = %s, summary = %s, end_time = NOW()
            WHERE meeting_id = %s
        """
        cursor.execute(sql, (status, transcript, summary, meeting_id))

def save_audio_chunk(meeting_id: str, chunk_number: int, chunk_timestamp: int, 
                     audio_data: bytes, sample_rate: int, transcript: str = None):
    """Save audio chunk to database"""
    with db.get_cursor() as cursor:
        sql = """
            INSERT INTO audio_chunks 
            (meeting_id, chunk_number, chunk_timestamp, audio_data, sample_rate, transcript_segment)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            audio_data = VALUES(audio_data),
            transcript_segment = VALUES(transcript_segment)
        """
        cursor.execute(sql, (meeting_id, chunk_number, chunk_timestamp, audio_data, sample_rate, transcript))
        
        # Update total chunks count
        sql_update = """
            UPDATE meetings 
            SET total_chunks = (SELECT COUNT(*) FROM audio_chunks WHERE meeting_id = %s)
            WHERE meeting_id = %s
        """
        cursor.execute(sql_update, (meeting_id, meeting_id))

def get_all_chunks(meeting_id: str):
    """Retrieve all audio chunks for a meeting"""
    with db.get_cursor() as cursor:
        sql = """
            SELECT chunk_number, transcript_segment, duration, chunk_timestamp
            FROM audio_chunks 
            WHERE meeting_id = %s 
            ORDER BY chunk_number
        """
        cursor.execute(sql, (meeting_id,))
        return cursor.fetchall()

def save_qa_interaction(meeting_id: str, question: str, answer: str, model_used: str, response_time: float):
    """Save Q&A interaction"""
    with db.get_cursor() as cursor:
        sql = """
            INSERT INTO qa_history (meeting_id, question, answer, model_used, response_time)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (meeting_id, question, answer, model_used, response_time))

def list_all_meetings():
    """List all meetings"""
    with db.get_cursor() as cursor:
        sql = """
            SELECT meeting_id, title, status, start_time, end_time, total_chunks
            FROM meetings 
            ORDER BY start_time DESC
        """
        cursor.execute(sql)
        return cursor.fetchall()

def log_system_event(level: str, message: str, meeting_id: str = None, stack_trace: str = None):
    """Log system event"""
    with db.get_cursor() as cursor:
        sql = """
            INSERT INTO system_logs (log_level, meeting_id, message, stack_trace)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (level, meeting_id, message, stack_trace))
