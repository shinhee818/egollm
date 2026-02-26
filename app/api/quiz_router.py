from app.services.quiz_evaluator import judge_blanks_with_llm
from fastapi import APIRouter
from pydantic import BaseModel, field_validator
from typing import List, Optional, Union, Any
import os
import json
import re
from openai import OpenAI
from app.services.quiz_service import QuizService
from app.core.llm_client import call_llm

router = APIRouter()

# -------------------------------------------------------
# DTO 정의
# -------------------------------------------------------
class BlankSlot(BaseModel):
    index: int
    placeholder: str
    answer: Optional[str] = None
    hint: Optional[str] = None


class FillInTheBlankQuizRequest(BaseModel):
    questionSentence: str  # 빈칸이 포함된 영어 문장
    userAnswers: Optional[Union[List[str], str]] = None  # 사용자 답안 (리스트 또는 띄어쓰기로 구분된 문자열)
    koreanSentence: Optional[str] = None  # 한글 원문 (선택적)
    originalSentence: Optional[str] = None  # 원본 완전한 영어 문장 (선택적, 없으면 questionSentence에서 재구성)
    blanks: Optional[Union[List[BlankSlot], List[Any], List[str]]] = None  # 선택적 (보내지 않아도 됨)
    
    @field_validator('originalSentence')
    @classmethod
    def validate_original_sentence(cls, v):
        # 빈 문자열이면 None으로 변환
        if v == "":
            return None
        return v
    
    @field_validator('blanks', mode='before')
    @classmethod
    def validate_blanks(cls, v):
        # blanks가 None이거나 빈 리스트면 None 반환
        if v is None or (isinstance(v, list) and len(v) == 0):
            return None
        # 리스트인 경우
        if isinstance(v, list):
            # 첫 번째 요소가 BlankSlot 객체면 그대로 반환
            if len(v) > 0 and isinstance(v[0], BlankSlot):
                return v
            # 첫 번째 요소가 딕셔너리면 BlankSlot로 변환 시도
            if len(v) > 0 and isinstance(v[0], dict):
                try:
                    return [BlankSlot(**item) for item in v if isinstance(item, dict)]
                except:
                    return None
            # 문자열이거나 다른 형식이면 None (잘못된 형식)
            return None
        return None


class TranslateSentenceQuizRequest(BaseModel):
    questionType: Optional[str] = None  # 선택적 필드 (호환성)
    koreanSentence: str
    userAnswer: Optional[str] = None
    correctAnswer: Optional[str] = None  # 퀴즈 생성 API에서 받은 정답


class MultipleChoiceQuizRequest(BaseModel):
    question: str
    options: List[str]
    selectedOption: Optional[str] = None


class QuizResponse(BaseModel):
    success: bool
    type: str
    result: dict



# -------------------------------------------------------
# 🎯 번역 퀴즈 (translate)
# -------------------------------------------------------
@router.post("/quiz/translate", response_model=QuizResponse)
def evaluate_translate(request: TranslateSentenceQuizRequest):
    user_answer = (request.userAnswer or "").strip()
    
    # 정답이 제공되었으면 사용, 없으면 LLM으로 생성
    if request.correctAnswer:
        correct_answer = request.correctAnswer
        prompt = f"Translate the following Korean sentence into natural English:\n{request.koreanSentence}"
    else:
        # 호환성을 위해 정답이 없으면 LLM으로 생성
        prompt = f"Translate the following Korean sentence into natural English:\n{request.koreanSentence}"
        correct_answer = call_llm(prompt)
    
    # 의미 기반 평가 및 피드백 생성
    evaluation = evaluate_translation_with_feedback(user_answer, correct_answer)

    result = {
        "prompt": prompt,
        "userAnswer": user_answer,
        "correctAnswer": correct_answer,
        "correct": evaluation["correct"],
        "feedback": evaluation["feedback"],
        "score": evaluation.get("score", "partial"),
    }

    return QuizResponse(success=True, type="translate", result=result)


# -------------------------------------------------------
# 🧩 빈칸 채우기 퀴즈 (blank)
# -------------------------------------------------------
@router.post("/quiz/blank", response_model=QuizResponse)
def evaluate_blank(request: FillInTheBlankQuizRequest):
    try:
        # 비즈니스 로직을 서비스로 위임
        result = QuizService.evaluate_blank_logic(request, call_llm)

        logger.info(f"Blank quiz evaluation successful for: {request.questionSentence[:30]}...")
        return QuizResponse(success=True, type="blank", result=result)

    except Exception as e:
        logger.error(f"Error in evaluate_blank: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="빈칸 퀴즈 평가 중 서버 오류가 발생했습니다.")


# -------------------------------------------------------
# 🧠 다지선다 퀴즈 (choice)
# -------------------------------------------------------
@router.post("/quiz/choice", response_model=QuizResponse)
def evaluate_choice(request: MultipleChoiceQuizRequest):
    prompt = (
        f"Choose the correct answer for the following question:\n"
        f"{request.question}\nOptions: {', '.join(request.options)}"
    )
    llm_answer = call_llm(prompt).strip()

    user_answer = (request.selectedOption or "").strip()
    correct = user_answer.lower() == llm_answer.lower()

    result = {
        "prompt": prompt,
        "userAnswer": user_answer,
        "llmAnswer": llm_answer,
        "correct": correct,
        "feedback": "Nice choice!" if correct else f"The correct answer is: {llm_answer}",
    }

    return QuizResponse(success=True, type="choice", result=result)