from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    type: str = Field(default="CHAT", description="요청 타입/ 항상 CHAT")
    prompt: str = Field(..., description="LLM에 전달될 전체 프롬프트")
    message: str = Field(..., description="사용자의 실제 메시지")
    userId: Optional[int] = Field(None, description="사용자 ID")
    sessionId: Optional[str] = Field(None, description="대화 세션 ID")

class ChatResult(BaseModel):
    message: str = Field(..., description="AI가 생성한 응답 메시지")
    sessionId: Optional[str] = Field(None, description="세션 ID")
    timestamp: int = Field(..., description="응답 생성 시간 (Unix timestamp, milliseconds)")

class ChatResponse(BaseModel):
    success: bool
    result: Optional[ChatResult] = None
    error: Optional[str] = None