from typing import Any, Dict, List, Optional, Sequence, Union
import json
import logging
import re

from app.services.llm_service import call_llm
from app.models.quiz_models import BlankSlot
logger = logging.getLogger(__name__)
# --- Constants ---
INVALID_ANSWERS = {"[blank]", "blank", ""}
RE_WORDS = re.compile(r'\b\w+\b')


def _normalize(s: Optional[str]) -> str:
    if s is None:
        return ""
    return " ".join(str(s).strip().lower().split())

def _is_valid_answer(answer: str) -> bool:
    return _normalize(answer) not in INVALID_ANSWERS

def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    if s in ("true", "1", "yes", "y", "t"):
        return True
    if s in ("false", "0", "no", "n", "f"):
        return False
    # fallback: non-empty string -> True
    return bool(s)


def _ensure_serial_blank(b: Any) -> Dict[str, Optional[str]]:
    if isinstance(b, dict):
        return {
            "index": b.get("index"),
            "placeholder": b.get("placeholder"),
            "answer": b.get("answer"),
            "hint": b.get("hint"),
        }
    # assume pydantic model or similar
    return {
        "index": getattr(b, "index", None),
        "placeholder": getattr(b, "placeholder", None),
        "answer": getattr(b, "answer", None),
        "hint": getattr(b, "hint", None),
    }


def _safe_json_load(s: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(s)
    except Exception:
        # try to locate JSON substring
        try:
            start = s.index("{")
            end = s.rindex("}") + 1
            return json.loads(s[start:end])
        except Exception:
            return None


def _is_valid_answer(answer: str) -> bool:
    """답안이 유효한지 확인 (BLANK, 빈 문자열 등 제외)"""
    if not answer:
        return False
    answer_clean = str(answer).strip()
    invalid_values = ["[BLANK]", "[blank]", "BLANK", "blank", ""]
    return answer_clean not in invalid_values and answer_clean.lower() not in invalid_values


def _clean_answers(answers: List[str]) -> List[str]:
    """답안 목록에서 유효하지 않은 값들을 제거"""
    return [ans for ans in answers if _is_valid_answer(ans)]


def _extract_answer_between_parts(original: str, part_before: str, part_after: str, start_pos: int) -> Optional[str]:
    """원본 문장에서 part_before와 part_after 사이의 답안 추출"""
    if not part_before.strip():
        return None
    
    original_lower = original.lower()
    part_before_lower = part_before.strip().lower()
    
    start = original_lower.find(part_before_lower, start_pos)
    if start == -1:
        return None
    
    answer_start = start + len(part_before.strip())
    
    if part_after.strip():
        part_after_lower = part_after.strip().lower()
        end = original_lower.find(part_after_lower, answer_start)
    else:
        end = len(original)
    
    if end == -1 and part_after.strip():
        return None
    
    answer_text = original[answer_start:end if end != -1 else len(original)].strip()
    
    # 단어만 추출
    words = re.findall(r'\b\w+\b', answer_text)
    if not words:
        return None
    
    answer = words[0] if len(words) == 1 else " ".join(words)
    return answer if _is_valid_answer(answer) else None


def _extract_answers_from_original_sentence(
    question_sentence: str,
    original_sentence: str
) -> List[str]:
    """
    정규식을 이용해 원본 문장에서 빈칸에 들어갈 단어를 추출합니다.
    [BLANK] 부분을 (.*?) 그룹으로 치환하여 매칭합니다.
    """
    if not original_sentence: return []

    # 1. [BLANK]를 정규식 캡처 그룹으로 변환 (특수문자 이스케이프 처리)
    pattern_str = re.escape(question_sentence).replace(r"\[BLANK\]", r"(.*?)")
    # 문장 끝 공백 등 미세한 차이 허용을 위해 앞뒤 공백 무시
    pattern = re.compile(f"^{pattern_str}$", re.IGNORECASE | re.DOTALL)

    match = pattern.match(original_sentence.strip())
    if match:
        extracted = [m.strip() for m in match.groups() if _is_valid_answer(m)]
        if len(extracted) == question_sentence.count("[BLANK]"):
            return extracted

    # 2. 실패 시 단어 차이(Diff) 기반 추출 (기존 로직 유지)
    q_words = set(_normalize(w) for w in question_sentence.replace("[BLANK]", " ").split())
    o_words = original_sentence.split()
    diff = [w for w in o_words if _normalize(w) not in q_words and _is_valid_answer(w)]

    return diff[:question_sentence.count("[BLANK]")]


def _get_correct_answers(
    blanks: Sequence[Dict[str, Optional[str]]],
    question_sentence: str,
    original_sentence: Optional[str]
) -> List[str]:
    """정답 목록 추출 (blanks 또는 originalSentence에서)"""
    # 먼저 blanks에서 정답 추출
    answers = [b.get("answer") or "" for b in blanks]
    answers = _clean_answers(answers)
    
    # 정답이 없거나 불완전하면 originalSentence에서 추출 시도
    if (not answers or len(answers) < question_sentence.count("[BLANK]")) and original_sentence:
        extracted = _extract_answers_from_original_sentence(question_sentence, original_sentence)
        if extracted:
            answers = extracted
            logger.info(f"Extracted correct answers from originalSentence: {answers}")
    
    return _clean_answers(answers)


def _build_sentence(template: str, answers: List[str], blanks: Optional[Sequence[Dict]] = None) -> str:
    """사용자 답안 또는 정답을 채운 완전한 문장 생성 (중복 로직 통합)"""
    sentence = template
    # index 기반 정렬이 필요한 경우 처리
    target_answers = answers
    if blanks:
        # index가 있는 경우 정렬된 순서대로 정답 배치
        sorted_blanks = sorted(blanks, key=lambda b: b.get("index", 0))
        target_answers = [next((ans for i, ans in enumerate(answers) if i == idx), "")
                          for idx, _ in enumerate(sorted_blanks)]

    for ans in target_answers:
        sentence = sentence.replace("[BLANK]", ans or "___", 1)
    return sentence


def _check_exact_match(
    user_sentence: str,
    original_sentence: str,
    correct_answers: List[str],
    user_answers: List[str],
    blank_count: int
) -> Optional[Dict[str, Any]]:
    """정확한 일치 여부 확인 (빠른 체크)"""
    if _normalize(user_sentence) == _normalize(original_sentence):
        return {
            "correct": True,
            "perBlank": [True] * blank_count,
            "feedback": "완벽합니다! 모든 빈칸이 정답입니다!",
            "llmFilled": correct_answers if correct_answers else user_answers
        }
    
    # 정답 목록과 정확히 일치하는지 확인
    if correct_answers:
        padded_user = user_answers + [""] * max(0, blank_count - len(user_answers))
        if len(correct_answers) == len(padded_user):
            if all(_normalize(ca) == _normalize(ua) for ca, ua in zip(correct_answers, padded_user)):
                return {
                    "correct": True,
                    "perBlank": [True] * blank_count,
                    "feedback": "완벽합니다! 모든 빈칸이 정답입니다!",
                    "llmFilled": correct_answers
                }
    
    return None


def _build_llm_prompt(
    original_sentence: str,
    user_sentence: str,
    korean_sentence: Optional[str]
) -> str:
    """LLM 평가를 위한 프롬프트 생성"""
    lines = [
        "You are a friendly English teacher evaluating fill-in-the-blank answers.",
        "Your goal is to encourage learning while being fair and generous in evaluation.",
        "",
        "You are given:",
        "1. The original complete English sentence (the correct answer)",
        "2. The student's complete sentence (with their answers filled in the blanks)",
        "3. The Korean translation of the original sentence",
        "",
        "Evaluate whether the student's sentence has the SAME MEANING as the original sentence.",
        "Be generous: if the meaning is the same or very similar, mark it as CORRECT.",
        "",
        "Return ONLY a JSON object with keys:",
        "  - perBlank: array of booleans (true if that blank's answer is acceptable)",
        "  - correct: boolean (true if the student's sentence has the same meaning as the original)",
        "  - feedback: short string explaining the evaluation, in Korean",
        "",
        f"Original sentence (correct answer): {original_sentence}",
        f"Student's sentence: {user_sentence}",
    ]
    
    if korean_sentence:
        lines.extend(["", f"Korean translation: {korean_sentence}"])
    
    lines.extend([
        "",
        "IMPORTANT EVALUATION RULES (Be generous and fair, but strict with nonsense):",
        "",
        "CRITICAL: If the student's answer contains random strings, gibberish, or meaningless words (like 'asdas', 'dasss', 'aaaa', etc.), mark as INCORRECT immediately.",
        "",
        "Then for valid answers:",
        "- Compare the MEANING of the two complete sentences",
        "- If the student's sentence conveys the SAME MEANING as the original, mark as CORRECT",
        "- Accept different word choices if they convey the same meaning (e.g., 'take' vs 'bring', 'visit' vs 'go to')",
        "- Accept minor grammatical variations if the meaning is clear",
        "- Accept synonyms and equivalent expressions",
        "- Only mark as incorrect if the meaning is clearly different OR if the answer is meaningless gibberish",
        "- Be generous with meaning, but strict: random strings and nonsense words must be marked as INCORRECT",
        "",
        "Examples:",
        "- Original: 'I visited a beach and enjoyed the scenery.'",
        "- Student: 'I went to a beach and enjoyed the beautiful scenery.' → CORRECT (same meaning)",
        "- Original: 'I need to buy ingredients for dinner.'",
        "- Student: 'I need to buy food for dinner.' → CORRECT (similar meaning)",
        "- Original: 'She enjoys reading novels.'",
        "- Student: 'She enjoys reading asdas.' → INCORRECT (meaningless word)",
        "",
        "Return valid JSON ONLY (no surrounding explanation).",
    ])
    
    return "\n".join(lines)


def _parse_llm_result(
    raw: str,
    blank_count: int,
    blanks: Sequence[Dict[str, Optional[str]]]
) -> Optional[Dict[str, Any]]:
    """LLM 응답 파싱 및 결과 반환"""
    parsed = _safe_json_load(raw)
    if not parsed or not isinstance(parsed, dict):
        return None
    
    correct_raw = parsed.get("correct")
    if correct_raw is None:
        return None
    
    overall = _to_bool(correct_raw)
    feedback = str(parsed.get("feedback", ""))
    
    blank_count_for_perblank = max(len(blanks), blank_count) if blanks else blank_count
    per_blank_raw = parsed.get("perBlank")
    
    if isinstance(per_blank_raw, list) and len(per_blank_raw) == blank_count_for_perblank:
        per_blank = [_to_bool(x) for x in per_blank_raw]
    else:
        per_blank = [overall] * blank_count_for_perblank
    
    return {
        "correct": bool(overall),
        "perBlank": per_blank,
        "feedback": feedback
    }


def _fallback_evaluation(
    user_sentence: str,
    original_sentence: str,
    correct_answers: List[str],
    user_answers: List[str],
    blank_count: int
) -> Dict[str, Any]:
    """LLM 평가 실패 시 폴백 평가 (단순 비교)"""
    # 문장 전체 비교
    if _normalize(user_sentence) == _normalize(original_sentence):
        return {
            "correct": True,
            "perBlank": [True] * blank_count,
            "feedback": "완벽합니다! 모든 빈칸이 정답입니다!",
            "llmFilled": correct_answers
        }
    
    # 개별 빈칸 비교
    padded_user = user_answers + [""] * max(0, blank_count - len(user_answers))
    per_blank = []
    feedback_items = []
    
    for i, (correct_ans, ua) in enumerate(zip(correct_answers, padded_user)):
        if not correct_ans:
            ok = bool(_normalize(ua))
        else:
            correct_norm = _normalize(correct_ans)
            user_norm = _normalize(ua)
            ok = (correct_norm == user_norm) or (correct_norm in user_norm) or (user_norm in correct_norm)
        
        per_blank.append(bool(ok))
        if not ok:
            feedback_items.append(
                f"빈칸 {i+1}: 정답은 '{correct_ans or '(없음)'}'인데 '{ua or '(답 없음)'}'를 입력하셨어요."
            )
    
    overall = all(per_blank)
    feedback = "모든 빈칸이 정답입니다!" if overall else " ".join(feedback_items)
    
    return {
        "correct": overall,
        "perBlank": per_blank,
        "feedback": feedback,
        "llmFilled": correct_answers
    }

# 평가 BLANK - 신희
def judge_blanks_with_llm(
    question_sentence: str,
    blanks: Sequence[Union[BlankSlot, Dict[str, Any]]],
    user_answers: List[str],
    korean_sentence: Optional[str] = None,
    original_sentence: Optional[str] = None,
) -> Dict[str, Any]:
    """
    빈칸 채우기 답안을 평가합니다.
    사용자 답을 빈칸에 넣어서 완전한 문장을 만들고,
    그 문장이 원본 영어 문장(original_sentence)과 의미가 같은지 평가합니다.

    반환 예시:
      {
        "correct": bool,
        "perBlank": [bool,...],
        "feedback": str,
        "llmFilled": [str,...]   # 정답 (blanks에서 가져온 answer)
      }
    """
    # 1. 데이터 준비 및 정규화
    serial_blanks = [_ensure_serial_blank(b) for b in blanks]
    blank_count = question_sentence.count("[BLANK]")

    # 2. 정답 후보군 확보
    correct_answers = _get_correct_answers(serial_blanks, question_sentence, original_sentence)

    # 3. 비교용 문장 생성
    user_sentence = _build_sentence(question_sentence, user_answers)
    final_original = original_sentence or _build_sentence(question_sentence, correct_answers)

    # 4. Fast Track: 정확히 일치하는지 확인
    exact_res = _check_exact_match(user_sentence, final_original, correct_answers, user_answers, blank_count)
    if exact_res: return exact_res

    # 5. LLM 평가
    prompt = _build_llm_prompt(final_original, user_sentence, korean_sentence)
    try:
        raw = call_llm(prompt)
        result = _parse_llm_result(raw, blank_count, serial_blanks)
        if result:
            return {**result, "llmFilled": correct_answers}
    except Exception as e:
        logger.error(f"LLM Judge failed: {e}")

    # 6. Fallback
    return _fallback_evaluation(user_sentence, final_original, correct_answers, user_answers, blank_count)
