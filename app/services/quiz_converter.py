import json
import logging
import random
import random
from typing import List, Optional, Dict, Any

# -------------------------------------------------------
#  통합 변환 엔트리 포인트
# -------------------------------------------------------

def convert_to_formatted_response(quiz: Dict[str, Any], quiz_type: str) -> Dict[str, Any]:
    """
    원본 퀴즈 데이터를 DSL 스펙과 Java DTO 형식으로 변환하여 반환합니다.
    """
    dsl_data = _convert_to_dsl_format(quiz, quiz_type)
    java_dto = _convert_to_java_dto_format(quiz, quiz_type, dsl_data)

    return {
        "dsl": dsl_data,
        "result": java_dto
    }
# -------------------------------------------------------
# 🎯 퀴즈 생성 API (퀴즈 타입별)
# -------------------------------------------------------

def _convert_to_dsl_format(quiz: dict, quiz_type: str) -> dict:
    """
    퀴즈 데이터를 DSL 스펙 형식으로 변환
  DSL 스펙:
    {
  "type": "BLANK | TRANSLATE | WORD"
      , "version": "1.0",
        "meta": {
            "difficulty": "EASY | MEDIUM | HARD",
            "tags": [],
            "note": ""
        },
        "body": {}
    }

    """
    difficulty_map = {
        "beginner": "EASY",
        "intermediate": "MEDIUM",
        "advanced": "HARD"
    }

    difficulty = difficulty_map.get(quiz.get("difficulty", "intermediate"), "MEDIUM")
    topic = quiz.get("topic")
    tags = [topic] if topic else []

    if quiz_type == "Translate":
        # TRANSLATE 타입 DSL 변환
        korean_sentence = quiz.get("koreanSentence", "")

        # 번역 정답 생성 (LLM으로)
        from app.services.llm_service import call_llm
        translation_prompt = f"Translate the following Korean sentence into natural English:\n{korean_sentence}"
        correct_answer = call_llm(translation_prompt)

        # 여러 정답 가능 (동의어, 유사 표현 등)
        answers = [correct_answer]

        # constraints는 hint나 topic 기반으로 생성
        constraints = []
        if topic:
            constraints.append(topic)

        return {
            "type": "TRANSLATE",
            "version": "1.0",
            "meta": {
                "difficulty": difficulty,
                "tags": tags,
                "note": ""
            },
            "body": {
                "koreanSentence": korean_sentence,
                "constraints": constraints,
                "answers": answers
            }
        }

    elif quiz_type == "Blank":
        # BLANK 타입 DSL 변환
        question_sentence = quiz.get("questionSentence", "")
        korean_sentence = quiz.get("koreanSentence", "")
        blanks = quiz.get("blanks", [])

        # [BLANK]를 ___로 변환 (DSL 스펙)
        sentence_with_underscores = question_sentence.replace("[BLANK]", "___")

        # blanks 배열을 DSL 형식으로 변환
        dsl_blanks = []
        for i, blank in enumerate(blanks):
            if hasattr(blank, "answer"):
                answer = blank.answer
            elif isinstance(blank, dict):
                answer = blank.get("answer")
            else:
                continue

            # answer가 문자열이면 리스트로 변환
            if isinstance(answer, str):
                answer_list = [answer]
            elif isinstance(answer, list):
                answer_list = answer
            else:
                answer_list = []

            # DSL 스펙: index는 1부터 시작
            blank_index = getattr(blank, "index", i) if hasattr(blank, "index") else blank.get("index", i) if isinstance(blank, dict) else i
            # index가 0부터 시작하면 1부터로 변환
            if blank_index == 0 or blank_index is None:
                blank_index = i + 1
            elif blank_index < 0:
                blank_index = i + 1

            dsl_blank = {
                "index": blank_index,
                "answer": answer_list,
                "explanation": getattr(blank, "hint", "") if hasattr(blank, "hint") else blank.get("hint", "") if isinstance(blank, dict) else ""
            }
            dsl_blanks.append(dsl_blank)

        return {
            "type": "BLANK",
            "version": "1.0",
            "meta": {
                "difficulty": difficulty,
                "tags": tags,
                "note": ""
            },
            "body": {
                "koreanHint": korean_sentence,
                "sentence": sentence_with_underscores,
                "blanks": dsl_blanks
            }
        }

    elif quiz_type == "SentenceArrange":
        # SENTENCE_ARRANGE 타입 DSL 변환
        question = quiz.get("question", "")
        korean_sentence = quiz.get("koreanSentence", "")
        words = quiz.get("words", [])
        shuffled_words = quiz.get("shuffledWords", [])
        correct_order = quiz.get("correctOrder", [])

        return {
            "type": "SENTENCE_ARRANGE",
            "version": "1.0",
            "meta": {
                "difficulty": difficulty,
                "tags": tags,
                "note": ""
            },
            "body": {
                "question": question,
                "koreanSentence": korean_sentence,
                "words": words,
                "shuffledWords": shuffled_words,
                "correctOrder": correct_order
            }
        }

    elif quiz_type == "Word" or quiz_type == "WORD":
        # WORD 타입 DSL 변환
        question = quiz.get("question", "")
        options = quiz.get("options", [])
        correct_option_id = quiz.get("correctOptionId") or quiz.get("correct_option_id")
        # refWordIds: 선택지와 연결된 사전 단어 ID 목록
        ref_word_ids = quiz.get("refWordIds") or quiz.get("ref_word_ids", [])

        # OptionItem을 Option으로 변환 (Java DTO 호환)
        dsl_options = []
        for option in options:
            if isinstance(option, dict):
                option_id = option.get("id")
                option_text = option.get("text")
            elif hasattr(option, "id") and hasattr(option, "text"):
                option_id = getattr(option, "id")
                option_text = getattr(option, "text")
            else:
                continue

            dsl_options.append({
                "id": option_id,
                "text": option_text
            })

        return {
            "type": "WORD",
            "version": "1.0",
            "meta": {
                "difficulty": difficulty,
                "tags": tags,
                "note": ""
            },
            "body": {
                "question": question,
                "options": dsl_options,
                "correctOptionId": correct_option_id or 1,
                "refWordIds": ref_word_ids if isinstance(ref_word_ids, list) else []
            }
        }

    else:
        raise ValueError(f"Unsupported quiz type: {quiz_type}")


def _convert_to_java_dto_format(quiz: dict, quiz_type: str, dsl_data: dict) -> dict:
    """
    DSL 데이터를 Java DTO 형식으로도 변환 (하위 호환성)

    GenerateQuizResult:
    {
        "quizType": "BLANK | TRANSLATE | WORD",
        "question": "string",
        "koreanSentence": "string",
        "answers": ["string"],
        "options": [...],  # WORD 타입만
        "correctOptionId": int,  # WORD 타입만
        "refWordIds": [...]  # optional
    }
    """
    if quiz_type == "Translate":
        body = dsl_data.get("body", {})
        return {
            "quizType": "TRANSLATE",
            "question": body.get("koreanSentence", ""),
            "koreanSentence": body.get("koreanSentence", ""),
            "answers": body.get("answers", [])
        }

    elif quiz_type == "Blank":
        body = dsl_data.get("body", {})
        blanks = body.get("blanks", [])

        # 모든 정답 수집
        all_answers = []
        for blank in blanks:
            answers = blank.get("answer", [])
            if isinstance(answers, list):
                all_answers.extend(answers)
            elif isinstance(answers, str):
                all_answers.append(answers)

        return {
            "quizType": "BLANK",
            "question": body.get("sentence", "").replace("___", "[BLANK]"),  # Java DTO는 [BLANK] 사용
            "koreanSentence": body.get("koreanHint", ""),
            "answers": all_answers
        }

    elif quiz_type == "Word" or quiz_type == "WORD":
        body = dsl_data.get("body", {})
        options = body.get("options", [])
        correct_option_id = body.get("correctOptionId", 1)
        ref_word_ids = body.get("refWordIds", [])

        # Option을 OptionItem으로 변환 (Java DTO 호환)
        option_items = []
        for option in options:
            if isinstance(option, dict):
                option_items.append({
                    "id": option.get("id"),
                    "text": option.get("text")
                })

        return {
            "quizType": "WORD",
            "question": body.get("question", ""),
            "options": option_items,  # OptionItem 형식
            "correctOptionId": correct_option_id,
            "refWordIds": ref_word_ids
        }

    elif quiz_type == "SentenceArrange":
        body = dsl_data.get("body", {})
        return {
            "quizType": "SENTENCE_ARRANGE",
            "question": body.get("question", ""),
            "koreanSentence": body.get("koreanSentence", ""),
            "words": body.get("words", []),
            "shuffledWords": body.get("shuffledWords", []),
            "correctOrder": body.get("correctOrder", [])
        }

    else:
        return {}


