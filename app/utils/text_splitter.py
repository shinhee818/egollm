# 사용자 답이 의미 없는지 체크

def is_meaningless_answer(answer: str) -> bool:
    if not answer or not answer.strip():
        return True

    import re
    answer_clean = answer.strip()

    # 한글 자모만 있는지 체크 (ㄱ, ㄴ, ㄷ, ㅂ, ㅈ 등)
    if re.match(r'^[ㄱ-ㅎㅏ-ㅣ\s]+$', answer_clean):
        return True

    # 같은 문자 반복 (예: "aaaa", "dddd")
    if len(set(answer_clean.lower())) <= 2 and len(answer_clean) >= 3:
        return True

    # 랜덤 문자열 패턴 체크 (자음만 반복되는 패턴)
    if re.match(r'^[bcdfghjklmnpqrstvwxyz]{3,}$', answer_clean.lower()):
        # 의미 있는 단어인지 간단 체크 (너무 짧거나 패턴이 이상하면)
        if len(answer_clean) <= 4 and not any(vowel in answer_clean.lower() for vowel in 'aeiou'):
            return True

    # 숫자만 있으면 의미 없음
    if re.match(r'^\d+$', answer_clean):
        return True

    return False