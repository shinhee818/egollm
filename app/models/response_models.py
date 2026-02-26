from pydantic import BaseModel, Field  # 이 줄이 빠져있을 겁니다!
from typing import Optional, List, Literal


# -------------------------------------------------------
# 응답 DTO (Response Models)
# -------------------------------------------------------
class ApiResponse(BaseModel):
    """스프링 부트 스타일 API 응답"""
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None


class MultipleQuizzesResponse(BaseModel):
    """여러 퀴즈 응답"""
    success: bool
    message: Optional[str] = None
    count: int
    quizType: str
    data: List[dict]

