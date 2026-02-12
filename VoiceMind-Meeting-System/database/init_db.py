"""
Database initialization script
"""
import mysql.connector
from mysql.connector import Error
import sys

# Configuration
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "root"  # Update with your MySQL root password

def init_database():
    """Initialize database from schema file"""
    try:
        # Connect to MySQL server (without database)
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Read and execute schema file
            print("📄 Reading schema file...")
            with open('database/schema.sql', 'r') as f:
                schema = f.read()
            
            # Split and execute statements
            statements = schema.split(';')
            
            for i, statement in enumerate(statements):
                statement = statement.strip()
                if statement:
                    try:
                        cursor.execute(statement)
                        print(f"✓ Executed statement {i+1}/{len(statements)}")
                    except Error as e:
                        if "already exists" not in str(e):
                            print(f"⚠️  Warning: {e}")
            
            connection.commit()
            print("\n✅ Database initialized successfully!")
            print("Database: voicemind_db")
            print("Tables: meetings, audio_chunks, qa_history, system_logs\n")
            
            cursor.close()
            connection.close()
    
    except Error as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print(" " * 15 + "VoiceMind Database Setup")
    print("=" * 60 + "\n")
    
    init_database()
