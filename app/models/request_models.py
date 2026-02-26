from pydantic import BaseModel, Field  # 이 줄이 빠져있을 겁니다!
from typing import Optional, List, Literal


# -------------------------------------------------------
# 요청 DTO (Request Models)
# -------------------------------------------------------
class GenerateQuizRequest(BaseModel):
    """퀴즈 생성 요청 (공통)"""
    quizType: Literal["Translate", "Blank","SentenceArrange"] = Field(..., description="퀴즈 타입: Translate 또는 Blank")
    difficulty: Optional[str] = Field("intermediate", description="난이도: beginner, intermediate, advanced")
    topic: Optional[str] = Field(None, description="주제 (예: 일상 대화, 비즈니스, 여행)")

    # Translate 퀴즈 전용 옵션
    length: Optional[str] = Field("short", description="Translate 퀴즈용 문장 길이: short, medium, long")

    # Blank 퀴즈 전용 옵션
    numBlanks: Optional[int] = Field(2, ge=1, le=5, description="Blank 퀴즈용 빈칸 개수 (1-5)")
    sentenceType: Optional[str] = Field("sentence", description="Blank 퀴즈용 문장 타입: sentence, paragraph")

    numWords: Optional[int] = Field(5, ge=3, le=10, description="SentenceArrange 퀴즈용 단어 개수")


class GenerateMultipleQuizzesRequest(BaseModel):
    """여러 퀴즈 일괄 생성 요청"""
    quizType: Literal["Translate", "Blank"] = Field(..., description="퀴즈 타입: Translate 또는 Blank")
    count: int = Field(5, ge=1, le=20, description="생성할 퀴즈 개수 (1-20)")
    difficulty: Optional[str] = Field("intermediate", description="난이도: beginner, intermediate, advanced")
    topic: Optional[str] = Field(None, description="주제")

    # Translate 퀴즈 전용 옵션
    length: Optional[str] = Field("short", description="Translate 퀴즈용 문장 길이: short, medium, long")

    # Blank 퀴즈 전용 옵션
    numBlanks: Optional[int] = Field(2, ge=1, le=5, description="Blank 퀴즈용 빈칸 개수 (1-5)")
    sentenceType: Optional[str] = Field("sentence", description="Blank 퀴즈용 문장 타입: sentence, paragraph")

