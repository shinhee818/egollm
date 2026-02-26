from pydantic import BaseModel, field_validator
from typing import List, Optional, Union, Any


# --- 공통 슬롯 ---
class BlankSlot(BaseModel):
    index: int
    placeholder: str
    answer: Optional[str] = None
    hint: Optional[str] = None


# --- 요청 모델 ---
class FillInTheBlankQuizRequest(BaseModel):
    questionSentence: str
    userAnswers: Optional[Union[List[str], str]] = None  # 리스트 또는 띄어쓰기로 구분된 문자열
    koreanSentence: Optional[str] = None  # 한글 원문 (선택적)
    originalSentence: Optional[str] = None  # 원본 완전한 영어 문장 (선택적, 없으면 questionSentence에서 재구성)
    blanks: Optional[Union[List[BlankSlot], List[Any], List[str]]] = None  # 선택적 (보내지 않아도 됨)

    @field_validator('originalSentence')
    @classmethod
    def validate_original_sentence(cls, v):
        if v == "":
            return None
        return v

    @field_validator('blanks', mode='before')
    @classmethod
    def validate_blanks(cls, v):
        if v is None or (isinstance(v, list) and len(v) == 0):
            return None
        if isinstance(v, list):
            if len(v) > 0 and isinstance(v[0], BlankSlot):
                return v
            if len(v) > 0 and isinstance(v[0], dict):
                try:
                    return [BlankSlot(**item) for item in v if isinstance(item, dict)]
                except:
                    return None
            return None
        return None


class TranslateSentenceQuizRequest(BaseModel):
    questionType: Optional[str] = None
    koreanSentence: str
    userAnswer: Optional[str] = None
    correctAnswer: Optional[str] = None


class MultipleChoiceQuizRequest(BaseModel):
    question: str
    options: List[str]
    selectedOption: Optional[str] = None


# --- 결과 모델 ---
class TranslateResult(BaseModel):
    prompt: str
    userAnswer: str
    correctAnswer: str
    correct: bool
    feedback: str
    score: Optional[str] = None  # "perfect", "good", "partial", "incorrect"


class BlankResult(BaseModel):
    prompt: str
    userAnswer: Optional[str] = None  # 호환성을 위해 문자열 형태도 지원
    userAnswers: List[str]
    correctAnswer: str  # 완전한 정답 문장
    correctWords: List[str]
    llmAnswer: Union[str, List[str]]  # 호환성을 위해 리스트도 지원
    correct: bool
    feedback: str
    perBlank: Optional[List[bool]] = None


class ChoiceResult(BaseModel):
    prompt: str
    options: List[str]
    selectedOption: Optional[str]
    correctAnswer: str
    correct: bool
    feedback: str


# --- 응답 모델 ---
class QuizResponse(BaseModel):
    success: bool
    type: str
    result: Union[TranslateResult, BlankResult, ChoiceResult, dict, None]
