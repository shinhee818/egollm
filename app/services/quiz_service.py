import logging
import logging
from typing import List, Optional, Any
from fastapi import HTTPException
from app.core.llm_client import call_llm

from app.utils.text_splitter import is_meaningless_answer
from app.services.quiz_evaluator import judge_blanks_with_llm, _extract_answers_from_original_sentence

logger = logging.getLogger(__name__)

class QuizService:
    @staticmethod
    def evaluate_blank_logic(request, call_llm_func) -> dict:
        """
        빈칸 퀴즈의 전처리, 평가, 후처리를 담당하는 핵심 로직
        """
        # 1. 사용자 답안 전처리 (문자열인 경우 리스트로 변환)
        user_words = QuizService._parse_user_answers(request.userAnswers)
        blanks = request.blanks or []

        # 2. 유효성 검사 (의미 없는 답안 체크)
        if any(is_meaningless_answer(str(ans)) for ans in user_words):
            return QuizService._build_meaningless_response(request.questionSentence, user_words)

        # 3. 원본 문장(정답 문장) 확보 로직
        original_sentence = QuizService._get_or_reconstruct_original(
            request.originalSentence, request.questionSentence, blanks
        )

        # 4. LLM 평가 엔진 호출
        judge = judge_blanks_with_llm(
            request.questionSentence,
            blanks,
            user_words,
            request.koreanSentence,
            original_sentence
        )

        # 5. 정답 단어(correct_words) 확정
        correct_words = QuizService._determine_correct_words(
            judge.get("llmFilled", []), blanks, request.questionSentence, original_sentence
        )

        # 6. 모범 답안 문장 생성 (빈칸이 모두 채워진 문장)
        correct_answer_sentence = QuizService._generate_final_correct_sentence(
            original_sentence, request.questionSentence, correct_words, call_llm_func
        )

        # 7. 결과 조립
        return {
            "prompt": request.questionSentence,
            "userAnswer": " ".join(user_words),
            "userAnswers": user_words,
            "correctAnswer": correct_answer_sentence,
            "correctWords": correct_words,
            "llmAnswer": correct_words, # 호환성 유지
            "correct": judge.get("correct", False),
            "feedback": judge.get("feedback", "평가 완료"),
            "perBlank": judge.get("perBlank", []),
        }

    # --- 내부 헬퍼 메서드들 ---

    @staticmethod
    def _parse_user_answers(user_answers_raw) -> List[str]:
        if isinstance(user_answers_raw, str):
            return [word.strip() for word in user_answers_raw.split() if word.strip()]
        return user_answers_raw or []

    @staticmethod
    def _build_meaningless_response(question, user_words):
        return {
            "prompt": question,
            "userAnswers": user_words,
            "correctWords": [],
            "correct": False,
            "feedback": "의미 있는 영어 단어를 입력해주세요. 랜덤 문자열이나 한글 자모는 평가할 수 없습니다.",
            "perBlank": [False] * len(user_words) if user_words else []
        }

    @staticmethod
    def _get_or_reconstruct_original(original, question, blanks):
        if original and original.strip():
            return original
        if not blanks:
            return question

        # blanks에서 재구성
        sorted_blanks = sorted(blanks, key=lambda b: getattr(b, "index", 0) if hasattr(b, "index") else 0)
        res = question
        for b in sorted_blanks:
            if hasattr(b, "answer") and b.answer:
                res = res.replace("[BLANK]", b.answer, 1)
        return res

    @staticmethod
    def _determine_correct_words(llm_filled, blanks, question, original):
        if llm_filled:
            return llm_filled

        # blanks에서 추출
        if blanks:
            words = [b.answer.strip() for b in blanks if hasattr(b, "answer") and b.answer]
            if words: return words

        # 원본 문장에서 추출 (마지막 수단)
        return _extract_answers_from_original_sentence(question, original)

    @staticmethod
    def _generate_final_correct_sentence(original, question, correct_words, call_llm_func):
        # 이미 완성된 문장이면 그대로 반환
        if original and "[BLANK]" not in original:
            return original

        # 정답 단어로 채우기 시도
        if correct_words:
            res = question
            for word in correct_words:
                res = res.replace("[BLANK]", word, 1)
            if "[BLANK]" not in res:
                return res

        # 최후의 수단: LLM에게 문장 완성 요청
        try:
            prompt = f"Fill in the blanks to make a natural sentence: '{question}'"
            res = call_llm_func(prompt, temperature=0.3).strip().replace('"', '')
            return res
        except:
            return question


    # -------------------------------------------------------
    # 의미 비교 및 피드백 생성
    # -------------------------------------------------------
    def evaluate_translation_with_feedback(user_answer: str, correct_answer: str) -> dict:
        """
        번역 답안을 평가하고 상세한 피드백을 제공

        Returns:
            {
                "correct": bool,  # 의미가 맞으면 True
                "feedback": str,   # 상세한 피드백
                "score": str       # "perfect", "good", "partial", "incorrect"
            }
        """
        prompt = f"""
    You are a friendly English teacher evaluating student translations.
    Your goal is to encourage learning while providing helpful feedback.
    
    Student's translation: "{user_answer}"
    Reference translation: "{correct_answer}"
    
    Evaluate the student's answer based on MEANING, not exact wording.
    
    IMPORTANT RULES:
    - If the meaning is the same or very similar, mark it as CORRECT
    - Accept different word choices if they convey the same meaning (e.g., "good" vs "clear" for weather descriptions)
    - Accept grammatical variations if the meaning is clear (e.g., "Today weather is good" vs "The weather is good today")
    - Ignore minor spelling mistakes, capitalization, and spacing differences
    - Be generous - if the student understood the meaning, they should get credit
    
    Return a JSON object with this structure:
    {{
        "correct": true or false,
        "score": "perfect" or "good" or "partial" or "incorrect",
        "feedback": "A friendly, encouraging feedback message in Korean. If correct, praise them. If incorrect, gently explain what could be improved. If partially correct, acknowledge what's right and suggest improvements."
    }}
    
    Examples:
    - If meaning is identical: {{"correct": true, "score": "perfect", "feedback": "완벽합니다! 정확한 번역이에요."}}
    - If meaning is similar but wording differs: {{"correct": true, "score": "good", "feedback": "좋아요! 의미는 정확하게 전달했어요. 더 자연스러운 표현: 'The weather is very clear today.'"}}
    - If meaning is partially correct: {{"correct": true, "score": "partial", "feedback": "의미는 이해하셨어요! 다만 '맑다'는 'clear'가 더 정확해요. 'good'도 괜찮지만 'very clear'가 원문의 의미에 더 가까워요."}}
    - If meaning is wrong: {{"correct": false, "score": "incorrect", "feedback": "의미가 조금 다르네요. '매우 맑아요'는 'very clear'를 의미해요. 다시 시도해보세요!"}}
    
    Return ONLY the JSON object, no other text.
    """
        result = call_llm(prompt, temperature=0.3)

        # JSON 파싱 시도
        # JSON 객체 찾기 (중첩된 객체도 처리)
        json_start = result.find('{')
        json_end = result.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            try:
                json_str = result[json_start:json_end]
                parsed = json.loads(json_str)
                return {
                    "correct": bool(parsed.get("correct", False)),
                    "feedback": parsed.get("feedback", "평가 중..."),
                    "score": parsed.get("score", "partial")
                }
            except json.JSONDecodeError:
                # 정규식으로 재시도
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*"correct"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        return {
                            "correct": bool(parsed.get("correct", False)),
                            "feedback": parsed.get("feedback", "평가 중..."),
                            "score": parsed.get("score", "partial")
                        }
                    except:
                        pass

        # 파싱 실패 시 폴백: 간단한 의미 비교
        simple_check = semantic_check_simple(user_answer, correct_answer)
        return {
            "correct": simple_check,
            "feedback": "좋은 시도예요! 의미를 잘 전달했어요." if simple_check else f"의미를 다시 확인해보세요. 참고: {correct_answer}",
            "score": "good" if simple_check else "partial"
        }


    def semantic_check_simple(user_answer: str, correct_answer: str) -> bool:
        """간단한 의미 비교 (폴백용)"""
        prompt = f"""
    Are these two sentences similar in meaning? Answer only "yes" or "no".
    
    Sentence 1: "{user_answer}"
    Sentence 2: "{correct_answer}"
    """
        result = call_llm(prompt, temperature=0.1)
        return "yes" in result.lower()
