from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import logging
from app.models.chat_models import ChatRequest, ChatResponse, ChatResult
from app.services.chat_service import chat_with_llm, clear_session, chat_with_llm_stream

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    영어 학습 튜터 AI와의 대화를 처리합니다.
    
    - **type**: 요청 타입 (항상 "CHAT")
    - **prompt**: LLM에 전달될 전체 프롬프트 (시스템 메시지 + 사용자 메시지)
    - **message**: 사용자의 실제 메시지
    - **userId**: 사용자 ID (선택)
    - **sessionId**: 대화 세션 ID (선택, 멀티턴 대화 시 사용)
    """
    try:
        if not request.message or not request.message.strip():
            return ChatResponse(
                success=False,
                error="Message cannot be empty"
            )
        
        system_prompt = None
        if request.prompt and "You are" in request.prompt:
            lines = request.prompt.split('\n')
            for line in lines:
                if line.strip().startswith("You are"):
                    system_prompt = line.strip()
                    break
        
        result_data = chat_with_llm(
            message=request.message,
            session_id=request.sessionId,
            user_id=request.userId,
            system_prompt=system_prompt
        )
        
        result = ChatResult(**result_data)
        
        return ChatResponse(
            success=True,
            result=result,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return ChatResponse(
            success=False,
            error=f"Chat generation failed: {str(e)}"
        )
    

@router.post("/chat/stream")
def chat_stream_endpoint(request: ChatRequest):
    """
    SSE 스트리밍 방식으로 AI와 대화합니다.
    
    - **type**: 요청 타입 (항상 "CHAT")
    - **prompt**: LLM에 전달될 전체 프롬프트
    - **message**: 사용자의 실제 메시지
    - **userId**: 사용자 ID (선택)
    - **sessionId**: 대화 세션 ID (선택)
    
    응답은 Server-Sent Events (SSE) 형식으로 스트리밍됩니다.
    """
    try:
        if not request.message or not request.message.strip():
            def error_gen():
                import json
                yield f"data: {json.dumps({'error': 'Message cannot be empty'})}\n\n"
            
            return StreamingResponse(
                error_gen(),
                media_type="text/event-stream"
            )
        
        system_prompt = None
        if request.prompt and "You are" in request.prompt:
            lines = request.prompt.split('\n')
            for line in lines:
                if line.strip().startswith("You are"):
                    system_prompt = line.strip()
                    break
        
        stream_gen = chat_with_llm_stream(
            message=request.message,
            session_id=request.sessionId,
            user_id=request.userId,
            system_prompt=system_prompt
        )
        
        return StreamingResponse(
            stream_gen,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Chat stream error: {e}")
        
        def error_gen():
            import json
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            error_gen(),
            media_type="text/event-stream"
        )



@router.delete("/chat/session/{session_id}")
def clear_chat_session(session_id: str):
    """
    특정 세션의 대화 이력을 삭제합니다.
    """
    success = clear_session(session_id)
    if success:
        return {"success": True, "message": f"Session {session_id} cleared"}
    else:
        return {"success": False, "message": f"Session {session_id} not found"}


@router.get("/chat/session/{session_id}")
def get_chat_session(session_id: str):
    """
    특정 세션의 대화 이력을 조회합니다.
    """
    from app.services.chat_service import get_session_history
    
    history = get_session_history(session_id)
    if history is not None:
        return {"success": True, "history": history}
    else:
        return {"success": False, "message": f"Session {session_id} not found"}