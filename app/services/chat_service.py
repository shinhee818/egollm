import time
import logging
from typing import Optional, Dict, List, Generator
from app.services.llm_service import call_llm, call_llm_stream

logger = logging.getLogger(__name__)

session_history: Dict[str, List[Dict[str, str]]] = {}

def chat_with_llm(
    message: str,
    session_id: Optional[str] = None,
    user_id: Optional[int] = None,
    system_prompt: Optional[str] = None
) -> Dict[str, any]:
    """
    LLM과 대화하고 응답을 반환합니다.
    
    Args:
        message: 사용자 메시지
        session_id: 세션 ID (None이면 단일 턴 대화)
        user_id: 사용자 ID (컨텍스트용)
        system_prompt: 시스템 프롬프트 (None이면 기본값 사용)
    
    Returns:
        {
            "message": str,
            "sessionId": str or None,
            "timestamp": int
        }
    """
    try:
        if not system_prompt:
            system_prompt = (
                "You are an English learning tutor. "
                "Provide helpful, encouraging, and educational responses. "
                "Keep your answers clear and appropriate for English learners."
            )
        
        if session_id and session_id in session_history:
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in session_history[session_id]
            ])
            full_prompt = f"{system_prompt}\n\nPrevious conversation:\n{history_text}\n\nUser: {message}\n\nAssistant:"
        else:
            full_prompt = f"{system_prompt}\n\nUser: {message}\n\nAssistant:"
        
        ai_message = call_llm(full_prompt, temperature=0.7)
        
        if session_id:
            if session_id not in session_history:
                session_history[session_id] = []
            
            session_history[session_id].append({"role": "user", "content": message})
            session_history[session_id].append({"role": "assistant", "content": ai_message})
            
            if len(session_history[session_id]) > 20:
                session_history[session_id] = session_history[session_id][-20:]
        
        return {
            "message": ai_message,
            "sessionId": session_id,
            "timestamp": int(time.time() * 1000)
        }
        
    except Exception as e:
        logger.error(f"Chat generation failed: {e}")
        raise

def chat_with_llm_stream(
    message: str,
    session_id: Optional[str] = None,
    user_id: Optional[int] = None,
    system_prompt: Optional[str] = None
) -> Generator[str, None, None]:
    """
    LLM과 스트리밍 대화하고 SSE 형식으로 청크를 생성합니다.
    
    Args:
        message: 사용자 메시지
        session_id: 세션 ID
        user_id: 사용자 ID
        system_prompt: 시스템 프롬프트
    
    Yields:
        SSE 형식의 청크 문자열 ("data: {chunk}\n\n")
    """
    try:
        if not system_prompt:
            system_prompt = (
                "You are an English learning tutor. "
                "Provide helpful, encouraging, and educational responses. "
                "Keep your answers clear and appropriate for English learners."
            )
        
        if session_id and session_id in session_history:
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in session_history[session_id]
            ])
            full_prompt = f"{system_prompt}\n\nPrevious conversation:\n{history_text}\n\nUser: {message}\n\nAssistant:"
        else:
            full_prompt = f"{system_prompt}\n\nUser: {message}\n\nAssistant:"
        
        full_response = ""
        
        for chunk in call_llm_stream(full_prompt, temperature=0.7):
            full_response += chunk
            yield f"data: {chunk}\n\n"
        
        if session_id:
            if session_id not in session_history:
                session_history[session_id] = []
            
            session_history[session_id].append({"role": "user", "content": message})
            session_history[session_id].append({"role": "assistant", "content": full_response})
            
            if len(session_history[session_id]) > 20:
                session_history[session_id] = session_history[session_id][-20:]
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Chat streaming failed: {e}")
        import json
        error_data = json.dumps({"error": str(e)})
        yield f"data: {error_data}\n\n"

def clear_session(session_id: str) -> bool:
    if session_id in session_history:
        del session_history[session_id]
        return True
    return False


def get_session_history(session_id: str) -> Optional[List[Dict[str, str]]]:
    return session_history.get(session_id)