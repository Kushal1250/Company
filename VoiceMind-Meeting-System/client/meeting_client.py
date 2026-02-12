"""
VoiceMind Meeting Client
Interactive command-line interface for querying meetings
"""
import requests
import json
from datetime import datetime
import sys

class MeetingClient:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        self.current_meeting = None
        print("=" * 70)
        print(" " * 15 + "VoiceMind Meeting Client")
        print("=" * 70 + "\n")
    
    def check_server(self):
        """Check if server is online"""
        try:
            response = requests.get(f"{self.server_url}/")
            if response.status_code == 200:
                print("✓ Connected to server\n")
                return True
        except:
            print("✗ Cannot connect to server. Please ensure server is running.\n")
            return False
    
    def list_meetings(self):
        """List all available meetings"""
        try:
            response = requests.get(f"{self.server_url}/api/list_meetings")
            data = response.json()
            meetings = data['meetings']
            
            print("\n" + "=" * 70)
            print(" " * 20 + "AVAILABLE MEETINGS")
            print("=" * 70)
            
            if not meetings:
                print("\nNo meetings found.")
            else:
                for i, meeting in enumerate(meetings, 1):
                    print(f"\n{i}. Meeting ID: {meeting['meeting_id']}")
                    print(f"   Title: {meeting['title'] or 'Untitled'}")
                    print(f"   Status: {meeting['status']}")
                    print(f"   Start Time: {meeting['start_time']}")
                    print(f"   Chunks: {meeting['total_chunks']}")
            
            print("\n" + "=" * 70)
            return meetings
        
        except Exception as e:
            print(f"✗ Error listing meetings: {e}")
            return []
    
    def select_meeting(self, meeting_id):
        """Select a meeting for analysis"""
        try:
            response = requests.get(f"{self.server_url}/api/get_summary?meeting_id={meeting_id}")
            if response.status_code == 200:
                self.current_meeting = meeting_id
                print(f"\n✓ Selected meeting: {meeting_id}")
                return True
            else:
                print(f"\n✗ Meeting not found: {meeting_id}")
                return False
        except Exception as e:
            print(f"✗ Error selecting meeting: {e}")
            return False
    
    def get_summary(self):
        """Get meeting summary"""
        if not self.current_meeting:
            print("❌ Please select a meeting first!")
            return
        
        try:
            response = requests.get(f"{self.server_url}/api/get_summary?meeting_id={self.current_meeting}")
            data = response.json()
            
            print("\n" + "=" * 70)
            print(" " * 25 + "MEETING SUMMARY")
            print("=" * 70)
            print(f"\nMeeting ID: {data['meeting_id']}")
            print(f"Title: {data['title'] or 'Untitled'}")
            print(f"Status: {data['status']}")
            print(f"Start Time: {data['start_time']}")
            print(f"End Time: {data['end_time']}")
            print(f"\n{'-' * 70}")
            print("SUMMARY:")
            print(f"{'-' * 70}")
            print(data['summary'])
            print(f"\n{'-' * 70}")
            print("AGENDA:")
            print(f"{'-' * 70}")
            print(data['agenda'])
            print("\n" + "=" * 70)
        
        except Exception as e:
            print(f"✗ Error getting summary: {e}")
    
    def get_transcript(self):
        """Get full meeting transcript"""
        if not self.current_meeting:
            print("❌ Please select a meeting first!")
            return
        
        try:
            response = requests.get(f"{self.server_url}/api/get_transcript?meeting_id={self.current_meeting}")
            data = response.json()
            
            print("\n" + "=" * 70)
            print(" " * 23 + "FULL TRANSCRIPT")
            print("=" * 70)
            
            for chunk in data['chunks']:
                timestamp = chunk['timestamp'] / 1000  # Convert to seconds
                print(f"\n[{timestamp:.1f}s] Chunk {chunk['chunk_number']}:")
                print(chunk['text'])
            
            print("\n" + "=" * 70)
        
        except Exception as e:
            print(f"✗ Error getting transcript: {e}")
    
    def ask_question(self, question):
        """Ask a question about the meeting"""
        if not self.current_meeting:
            print("❌ Please select a meeting first!")
            return
        
        try:
            payload = {
                "meeting_id": self.current_meeting,
                "question": question
            }
            
            print("\n⏳ Processing your question...")
            response = requests.post(f"{self.server_url}/api/ask_question", params=payload)
            data = response.json()
            
            print("\n" + "-" * 70)
            print(f"❓ Q: {question}")
            print(f"\n💡 A: {data['answer']}")
            print(f"\n⏱️  Response time: {data['response_time']:.2f}s")
            print("-" * 70)
        
        except Exception as e:
            print(f"✗ Error asking question: {e}")
    
    def interactive_mode(self):
        """Run interactive Q&A session"""
        print("\n" + "=" * 70)
        print(" " * 20 + "INTERACTIVE MODE")
        print("=" * 70)
        print("\nCommands:")
        print("  'list'           - List all meetings")
        print("  'select <id>'    - Select a meeting")
        print("  'summary'        - Get meeting summary")
        print("  'transcript'     - Get full transcript")
        print("  'exit' or 'quit' - Exit interactive mode")
        print("  Any other text   - Ask question about current meeting")
        print("\n" + "=" * 70)
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit']:
                    print("\nGoodbye! 👋\n")
                    break
                
                elif user_input.lower() == 'list':
                    self.list_meetings()
                
                elif user_input.lower().startswith('select '):
                    meeting_id = user_input[7:].strip()
                    self.select_meeting(meeting_id)
                
                elif user_input.lower() == 'summary':
                    self.get_summary()
                
                elif user_input.lower() == 'transcript':
                    self.get_transcript()
                
                else:
                    # Treat as question
                    self.ask_question(user_input)
            
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋\n")
                break
            except Exception as e:
                print(f"\n✗ Error: {e}")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Get server URL from command line argument or use default
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    client = MeetingClient(server_url)
    
    if not client.check_server():
        sys.exit(1)
    
    # Auto-list meetings on startup
    meetings = client.list_meetings()
    
    # If meetings exist, auto-select the first one
    if meetings:
        client.select_meeting(meetings[0]['meeting_id'])
    
    # Start interactive mode
    client.interactive_mode()
