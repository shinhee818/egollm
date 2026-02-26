"""
퀴즈 제네레이터 API 라우터
스프링 부트 스타일의 RESTful API 엔드포인트
퀴즈 타입: Translate, Blank
"""

from fastapi import APIRouter, Query, HTTPException, Path
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum
import logging
from app.services.quiz_generator import (
    QuizGeneratorService,
    generate_translate_quiz,
    generate_blank_quiz,
    generate_sentence_arrange_quiz
)
from app.models.request_models import (
    GenerateQuizRequest,
    GenerateMultipleQuizzesRequest
)
from app.models.response_models import (
    ApiResponse,
    MultipleQuizzesResponse
)
from app.services import quiz_converter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quiz", tags=["Quiz Generator"])

# -------------------------------------------------------
# 퀴즈 타입 Enum
# -------------------------------------------------------
class QuizType(str, Enum):
    """지원하는 퀴즈 타입"""
    TRANSLATE = "Translate"
    BLANK = "Blank"


def _handle_single_generation(quiz_type: str, params: dict):
    """단일 퀴즈 생성 및 변환 공통 로직"""
    try:
        # 1. 생성
        quiz = QuizGeneratorService.create_quiz(quiz_type=quiz_type, **params)
        # 2. 변환 (DSL + Java DTO)
        return quiz_converter.convert_to_formatted_response(quiz, quiz_type)
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/quiz/generate")
def generate_quiz(request: GenerateQuizRequest):
    """
    퀴즈 타입에 따라 퀴즈 생성 (통합 엔드포인트)
    DSL 스펙 및 Java DTO 호환 응답 포맷
    
    퀴즈 타입: Translate, Blank
    
    응답 형식:
    {
        "success": true,
        "type": "Translate | Blank",
        "dsl": { ... },  # DSL 스펙 형식
        "result": { ... }  # Java DTO 호환 형식
    }
    
    예시 (Translate):
        POST /api/quiz/generate
        Body: {
            "quizType": "Translate",
            "difficulty": "intermediate",
            "topic": "일상 대화",
            "length": "medium"
        }
    
    예시 (Blank):
        POST /api/quiz/generate
        Body: {
            "quizType": "Blank",
            "difficulty": "beginner",
            "topic": "여행",
            "numBlanks": 2,
            "sentenceType": "sentence"
        }
    """
    params = request.model_dump(exclude={"quizType"}, exclude_none=True)
    result = _handle_single_generation(request.quizType, params)

    return {
        "success": True,
        "type": request.quizType,
        **result
    }


@router.get("/generate/{quiz_type}", response_model=ApiResponse)
def generate_quiz_by_type(
        quiz_type: Literal["Translate", "Blank", "SentenceArrange"] = Path(...),
        difficulty: str = Query("intermediate"),
        topic: Optional[str] = Query(None),
        **kwargs  # 나머지 쿼리 파라미터(numBlanks, length 등)를 자동으로 받음
):
    """
    GET 방식으로 퀴즈 타입별 퀴즈 생성
    DSL 스펙 및 Java DTO 호환 응답 포맷
    
    예시 (Translate):
        GET /api/quiz/generate/Translate?difficulty=intermediate&topic=일상 대화&length=medium
    
    예시 (Blank):
        GET /api/quiz/generate/Blank?difficulty=beginner&numBlanks=2&sentenceType=sentence
    """
    params = {"difficulty": difficulty, "topic": topic, **kwargs}
    result = _handle_single_generation(quiz_type, params)

    return ApiResponse(
        success=True,
        message=f"{quiz_type} 퀴즈가 성공적으로 생성되었습니다.",
        data=result
    )


# -------------------------------------------------------
# 📦 여러 퀴즈 일괄 생성 API
# -------------------------------------------------------

@router.post("/generate/multiple", response_model=MultipleQuizzesResponse)
def generate_multiple_quizzes(request: GenerateMultipleQuizzesRequest):
    """
    여러 개의 퀴즈를 한번에 생성
    
    예시:
        POST /api/quiz/generate/multiple
        Body: {
            "quizType": "Translate",
            "count": 5,
            "difficulty": "intermediate",
            "topic": "일상 대화",
            "length": "medium"
        }
    """
    params = request.model_dump(exclude={"quizType", "count"}, exclude_none=True)

    quizzes = QuizGeneratorService.generate_multiple_quizzes(
        quiz_type=request.quizType,
        count=request.count,
        **params
    )

    # 각 퀴즈 변환
    formatted_list = [
        quiz_converter.convert_to_formatted_response(q, request.quizType)
        for q in quizzes
    ]

    return MultipleQuizzesResponse(
        success=True,
        message=f"{len(quizzes)}개의 퀴즈가 생성되었습니다.",
        count=len(quizzes),
        quizType=request.quizType,
        data={
            "dsl": [item["dsl"] for item in formatted_list],
            "result": [item["result"] for item in formatted_list]
        }
    )


@router.get("/api/quiz/generate/multiple/{quiz_type}", response_model=MultipleQuizzesResponse)
def generate_multiple_quizzes_get(
        quiz_type: Literal["Translate", "Blank", "SentenceArrange"] = Path(...),
        count: int = Query(5, ge=1, le=20),
        **kwargs  # difficulty, topic, length, numBlanks 등을 모두 dict로 받음
):
    """
    GET 방식으로 여러 개의 퀴즈를 한번에 생성 (퀴즈 타입별)
    
    예시 (Translate):
        GET /api/quiz/generate/multiple/Translate?count=5&difficulty=intermediate
    
    예시 (Blank):
        GET /api/quiz/generate/multiple/Blank?count=5&numBlanks=2
    """
    try:
        # 1. 서비스 호출 (kwargs에 모든 쿼리 파라미터가 들어있으므로 그대로 전달)
        quizzes = QuizGeneratorService.generate_multiple_quizzes(
            quiz_type=quiz_type,
            count=count,
            **kwargs
        )

        if not quizzes:
            raise HTTPException(status_code=500, detail="퀴즈 생성 실패")

        # 2. 통합 변환 로직 적용 (List Comprehension으로 간결하게)
        formatted_list = [
            quiz_converter.convert_to_formatted_response(q, quiz_type)
            for q in quizzes
        ]

        # 3. 응답 반환
        return MultipleQuizzesResponse(
            success=True,
            message=f"{len(quizzes)}개의 퀴즈가 생성되었습니다.",
            count=len(quizzes),
            quizType=quiz_type,
            data={
                "dsl": [item["dsl"] for item in formatted_list],
                "result": [item["result"] for item in formatted_list]
            }
        )
    except Exception as e:
        logger.error(f"Multiple generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

