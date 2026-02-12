"""
AI-powered Question Answering service using OpenAI GPT
"""
import openai
import logging
import time
from config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE, MAX_TOKENS

openai.api_key = OPENAI_API_KEY
logger = logging.getLogger(__name__)

def answer_question(transcript: str, question: str):
    """
    Answer questions about the meeting transcript using GPT
    
    Args:
        transcript: Full meeting transcript
        question: User question
    
    Returns:
        dict: Answer and metadata
    """
    start_time = time.time()
    
    try:
        system_prompt = """You are an AI meeting assistant. Your task is to answer questions about meetings based on the provided transcript. 
        
Guidelines:
- Be concise and accurate
- Quote relevant parts of the transcript when applicable
- If the answer is not in the transcript, say so clearly
- Extract action items, decisions, and key points when asked
- Identify speakers if mentioned in the transcript"""

        user_prompt = f"""Meeting Transcript:
{transcript}

Question: {question}

Please provide a clear and helpful answer based on the transcript."""

        response = openai.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        
        answer = response.choices[0].message.content
        response_time = time.time() - start_time
        
        logger.info(f"Q&A completed in {response_time:.2f}s")
        
        return {
            'answer': answer,
            'model': LLM_MODEL,
            'response_time': response_time,
            'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else None
        }
    
    except Exception as e:
        logger.error(f"Q&A error: {e}")
        return {
            'answer': f"Error generating answer: {str(e)}",
            'model': LLM_MODEL,
            'response_time': time.time() - start_time,
            'error': str(e)
        }

def generate_summary(transcript: str):
    """Generate meeting summary"""
    return answer_question(
        transcript,
        "Please provide a comprehensive summary of this meeting including key discussion points, decisions made, and any action items."
    )

def extract_agenda(transcript: str):
    """Extract meeting agenda"""
    return answer_question(
        transcript,
        "What was the agenda of this meeting? List the main topics discussed."
    )

def extract_action_items(transcript: str):
    """Extract action items"""
    return answer_question(
        transcript,
        "Extract all action items, tasks, and follow-ups mentioned in this meeting. Format as a list with responsible persons if mentioned."
    )
