-- ============================================================================
-- VoiceMind Meeting Intelligence System - MySQL Database Schema
-- ============================================================================

-- Drop existing database if exists (WARNING: This deletes all data!)
DROP DATABASE IF EXISTS voicemind_db;

-- Create database
CREATE DATABASE voicemind_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE voicemind_db;

-- ============================================================================
-- TABLE: meetings
-- Stores meeting metadata and full transcripts
-- ============================================================================
CREATE TABLE meetings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    meeting_id VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255),
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME NULL,
    status ENUM('recording', 'processing', 'completed', 'failed') DEFAULT 'recording',
    language VARCHAR(10) DEFAULT 'auto',
    full_transcript TEXT,
    summary TEXT,
    agenda TEXT,
    total_chunks INT DEFAULT 0,
    total_duration FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_meeting_id (meeting_id),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE: audio_chunks
-- Stores individual audio segments with transcriptions
-- ============================================================================
CREATE TABLE audio_chunks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    meeting_id VARCHAR(100) NOT NULL,
    chunk_number INT NOT NULL,
    chunk_timestamp BIGINT NOT NULL,
    audio_data LONGBLOB,
    audio_file_path VARCHAR(500),
    sample_rate INT DEFAULT 16000,
    duration FLOAT,
    transcript_segment TEXT,
    language_detected VARCHAR(10),
    confidence_score FLOAT,
    speaker_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    UNIQUE KEY unique_chunk (meeting_id, chunk_number),
    INDEX idx_meeting_chunks (meeting_id, chunk_number),
    INDEX idx_timestamp (chunk_timestamp)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE: qa_history
-- Stores question-answer interactions for each meeting
-- ============================================================================
CREATE TABLE qa_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    meeting_id VARCHAR(100) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    context_used TEXT,
    model_used VARCHAR(50),
    response_time FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    INDEX idx_meeting_qa (meeting_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE: system_logs
-- Stores system events and errors
-- ============================================================================
CREATE TABLE system_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    log_level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') DEFAULT 'INFO',
    meeting_id VARCHAR(100),
    message TEXT NOT NULL,
    stack_trace TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_log_level (log_level),
    INDEX idx_meeting_logs (meeting_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- ============================================================================
-- VIEWS: Useful aggregated views
-- ============================================================================

-- View: Meeting statistics
CREATE VIEW meeting_stats AS
SELECT 
    m.meeting_id,
    m.title,
    m.status,
    m.start_time,
    m.end_time,
    TIMESTAMPDIFF(MINUTE, m.start_time, m.end_time) AS duration_minutes,
    m.total_chunks,
    COUNT(ac.id) AS chunks_stored,
    SUM(ac.duration) AS total_audio_duration,
    COUNT(qa.id) AS questions_asked
FROM meetings m
LEFT JOIN audio_chunks ac ON m.meeting_id = ac.meeting_id
LEFT JOIN qa_history qa ON m.meeting_id = qa.meeting_id
GROUP BY m.meeting_id;

-- ============================================================================
-- STORED PROCEDURES
-- ============================================================================

DELIMITER //

-- Procedure: Get meeting summary with statistics
CREATE PROCEDURE GetMeetingSummary(IN p_meeting_id VARCHAR(100))
BEGIN
    SELECT 
        m.*,
        COUNT(ac.id) AS total_chunks_stored,
        SUM(ac.duration) AS total_duration_seconds,
        COUNT(DISTINCT ac.language_detected) AS languages_detected,
        COUNT(qa.id) AS total_questions_asked
    FROM meetings m
    LEFT JOIN audio_chunks ac ON m.meeting_id = ac.meeting_id
    LEFT JOIN qa_history qa ON m.meeting_id = qa.meeting_id
    WHERE m.meeting_id = p_meeting_id
    GROUP BY m.id;
END //

-- Procedure: Clean up old meetings (older than 30 days)
CREATE PROCEDURE CleanupOldMeetings()
BEGIN
    DELETE FROM meetings 
    WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
    AND status = 'completed';
END //

DELIMITER ;

-- ============================================================================
-- INITIAL DATA (Optional test data)
-- ============================================================================

-- Insert sample meeting for testing
INSERT INTO meetings (meeting_id, title, status) 
VALUES ('test_meeting_001', 'Test Meeting', 'recording');

-- ============================================================================
-- GRANT PERMISSIONS (Adjust username/password as needed)
-- ============================================================================

-- Create application user (run this separately after database creation)
-- CREATE USER 'voicemind_user'@'localhost' IDENTIFIED BY 'your_secure_password';
-- GRANT ALL PRIVILEGES ON voicemind_db.* TO 'voicemind_user'@'localhost';
-- FLUSH PRIVILEGES;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
