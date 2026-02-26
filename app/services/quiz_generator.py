"""
퀴즈 제네레이터 서비스
Translate, Blank 퀴즈를 생성하는 비즈니스 로직
"""

import json
import logging
import random
import random
from typing import List, Optional, Dict, Any
from app.services.llm_service import call_llm
from app.services.generators.sentence_arrange_generator import SentenceArrangeGenerator
from app.services.generators.translate_generator import TranslateGenerator
from app.services.generators.blank_generator import BlankGenerator
from app.services.generators import registry as generator_registry
from app.models.quiz_models import BlankSlot
logger = logging.getLogger(__name__)

class QuizGeneratorService:

    @staticmethod
    def create_quiz(quiz_type: str, **kwargs) -> Dict[str, Any]:
        """
        단일 퀴즈 생성 통합 메서드
        """
        gen_cls = generator_registry.get_generator(quiz_type)
        if not gen_cls:
            supported = list(generator_registry._REGISTRY.keys())
            raise ValueError(f"지원하지 않는 퀴즈 타입: {quiz_type}. 지원 목록: {supported}")

        # 개별 Generator의 generate 메서드 호출
        # kwargs에 포함된 파라미터들이 각 Generator의 인자로 들어감
        return gen_cls.generate(**kwargs)


    """퀴즈 생성 비즈니스 로직"""
    @staticmethod
    def generate_sentence_arrange_quiz(
        difficulty: str = "intermediate",
        topic: Optional[str] = None,
        num_words: int = 5
    ) -> Dict[str, Any]:
        """
        문장 배열(Sentence Arrange) 퀴즈 생성
        
        LLM이 영문 문장을 생성하고, 단어를 섞은 뒤
        correctOrder 배열로 정답 순서를 제공합니다.
        
        Args:
            difficulty: 난이도 (beginner, intermediate, advanced)
            topic: 주제
            num_words: 단어 개수 (3-10 추천)
        
        Returns:
            {
                "questionType": "SentenceArrange",
                "question": "완전한 영문 문장",
                "koreanSentence": "한국어 번역",
                "words": ["word1", "word2", ...],  # 정답 순서
                "shuffledWords": ["word3", "word1", ...],  # 섞인 순서
                "correctOrder": [1, 0, 2, ...],  # shuffledWords → words 인덱스
                "difficulty": str,
                "topic": str
            }
        """
        # Delegate to extracted generator for better testability and separation
        return SentenceArrangeGenerator.generate(difficulty=difficulty, topic=topic, num_words=num_words)

    @staticmethod
    def generate_translate_quiz(
        difficulty: str = "intermediate",
        topic: Optional[str] = None,
        length: str = "short"
    ) -> Dict[str, Any]:
        """
        번역 퀴즈 생성
        
        Args:
            difficulty: 난이도 (beginner, intermediate, advanced)
            topic: 주제 (예: "일상 대화", "비즈니스", "여행" 등, None이면 랜덤)
            length: 문장 길이 (short, medium, long)
        
        Returns:
            {
                "koreanSentence": str,
                "hint": Optional[str],
                "difficulty": str,
                "topic": Optional[str]
            }
        """
        # Delegate to TranslateGenerator
        return TranslateGenerator.generate(difficulty=difficulty, topic=topic, length=length)

    @staticmethod
    def generate_blank_quiz(
        difficulty: str = "intermediate",
        topic: Optional[str] = None,
        num_blanks: int = 2,
        sentence_type: str = "sentence"  # sentence, paragraph
    ) -> Dict[str, Any]:
        """
        빈칸 채우기 퀴즈 생성
        
        Args:
            difficulty: 난이도 (beginner, intermediate, advanced)
            topic: 주제 (예: "일상 대화", "비즈니스", "여행" 등, None이면 랜덤)
            num_blanks: 빈칸 개수 (1-5개 권장)
            sentence_type: 문장 타입 (sentence: 단일 문장, paragraph: 여러 문장)
        
        Returns:
            {
                "questionSentence": str,  # 빈칸이 포함된 영어 문장
                "koreanSentence": str,    # 한국어 번역/해석
                "blanks": List[BlankSlot],
                "difficulty": str,
                "topic": Optional[str]
            }
        """
        # Delegate to BlankGenerator
        return BlankGenerator.generate(difficulty=difficulty, topic=topic, num_blanks=num_blanks, sentence_type=sentence_type)

    @staticmethod
    def generate_multiple_quizzes(
            quiz_type: str,
            count: int = 5,
            **kwargs
    ) -> List[Dict[str, Any]]:
        """
        여러 개의 퀴즈를 일괄 생성 (create_quiz 재사용)
        """
        quizzes = []
        for i in range(count):
            try:
                quiz = QuizGeneratorService.create_quiz(quiz_type, **kwargs)
                quizzes.append(quiz)
            except Exception as e:
                logger.error(f"Error generating quiz {i+1}/{count} for type {quiz_type}: {e}")
                continue

        return quizzes


def generate_translate_quiz(**kwargs) -> Dict[str, Any]:
    return QuizGeneratorService.create_quiz("translate", **kwargs)

def generate_blank_quiz(**kwargs) -> Dict[str, Any]:
    return QuizGeneratorService.create_quiz("blank", **kwargs)

def generate_sentence_arrange_quiz(**kwargs) -> Dict[str, Any]:
    return QuizGeneratorService.create_quiz("sentencearrange", **kwargs)
