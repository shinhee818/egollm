"""Blank quiz generator module.

Extracted from QuizGeneratorService.generate_blank_quiz.
"""

import json
import logging
import random
from typing import Optional, Dict, Any, List
from app.services.llm_service import call_llm
from app.models.quiz_models import BlankSlot

logger = logging.getLogger(__name__)


class BlankGenerator:
    @staticmethod
    def _parse_json_response(response: str) -> Dict[str, Any]:
        resp = response.strip()
        if "```json" in resp:
            start = resp.find("```json") + 7
            end = resp.find("```", start)
            resp = resp[start:end].strip()
        elif "```" in resp:
            start = resp.find("```") + 3
            end = resp.find("```", start)
            resp = resp[start:end].strip()

        start = resp.find("{")
        end = resp.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in response")
        json_str = resp[start:end]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, response: {response}")
            raise ValueError(f"Failed to parse JSON: {e}")

    @staticmethod
    def generate(difficulty: str = "intermediate", topic: Optional[str] = None, num_blanks: int = 2, sentence_type: str = "sentence") -> Dict[str, Any]:
        try:
            num_blanks = max(1, min(5, num_blanks))

            prompt_parts = [
                "You are an English tutor creating fill-in-the-blank quizzes for Korean learners.",
                f"Generate a {difficulty} level English {'sentence' if sentence_type == 'sentence' else 'paragraph'} with {num_blanks} blank(s).",
                "IMPORTANT: Create a DIFFERENT and VARIED sentence each time. Avoid repeating similar sentences.",
                "Use diverse topics, sentence structures, and vocabulary to ensure variety.",
            ]

            if topic:
                prompt_parts.append(f"Topic: {topic}")
            else:
                prompt_parts.append("Choose a random topic (daily conversation, hobbies, travel, work, food, weather, etc.)")

            prompt_parts.extend([
                "",
                "STEP-BY-STEP PROCESS (Follow this exactly):",
                "",
                "Step 1: Create a complete, natural English sentence first.",
                f"Step 2: From that complete sentence, randomly select exactly {num_blanks} word(s) or phrase(s) to turn into blanks.",
                "Step 3: Replace those selected words/phrases with [BLANK] in the sentence.",
                "Step 4: The 'answer' for each blank MUST be the exact original word/phrase from the complete sentence you created.",
                "",
                "Requirements:",
                f"- Create a complete English {'sentence' if sentence_type == 'sentence' else 'paragraph (2-3 sentences)'} FIRST",
                f"- Then replace exactly {num_blanks} word(s)/phrase(s) with [BLANK]",
                "- The blanks should test important vocabulary, grammar, or expressions",
                "- Provide the Korean translation/interpretation of the COMPLETE original sentence",
                "- The answer for each blank MUST be the exact word/phrase that was in the original complete sentence",
                "- Optionally provide hints for each blank",
                "",
                "Return ONLY a JSON object with the following structure:",
                '{',
                '  "originalSentence": "원본 완전한 영어 문장 (빈칸 없음)",',
                '  "questionSentence": "영어 문장에서 [BLANK]로 빈칸 표시 (원래 문장에서 단어를 [BLANK]로 바꾼 것)",',
                '  "koreanSentence": "완전한 한국어 번역/해석 (빈칸 없이 전체 문장, 원래 완전한 문장의 번역)",',
                '  "blanks": [',
                '    {',
                '      "index": 0,',
                '      "placeholder": "[BLANK]",',
                '      "answer": "정답 단어/구 (원래 완전한 문장에 있던 정확한 단어/구)",',
                '      "hint": "힌트 (선택사항)"',
                '    }',
                '  ],',
                '  "difficulty": "beginner/intermediate/advanced",',
                '  "topic": "주제"',
                '}',
                "",
                "CRITICAL RULES:",
                "- questionSentence의 [BLANK]를 answer로 채우면 원래 완전한 문장이 되어야 합니다.",
                "- answer는 반드시 questionSentence에서 [BLANK]로 바꾸기 전 원래 문장에 있던 정확한 단어/구여야 합니다.",
                "- koreanSentence는 빈칸이 없는 완전한 문장의 번역이어야 합니다.",
                "- questionSentence에서 [BLANK]를 answer로 치환하면 자연스러운 완전한 영어 문장이 되어야 합니다.",
                "",
                "Example:",
                "- Original sentence: 'I need to buy some ingredients for dinner.'",
                "- After making blanks: 'I need to buy some [BLANK] for [BLANK].'",
                "- Answers: ['ingredients', 'dinner']",
                "- Korean: '저녁을 위해 재료를 좀 사야 해요.'",
                "",
                "Do not include any explanation, only the JSON object."
            ])

            prompt = "\n".join(prompt_parts)
            response = call_llm(prompt, temperature=0.8)
            result = BlankGenerator._parse_json_response(response)

            if "questionSentence" not in result or not result["questionSentence"]:
                raise ValueError("Failed to generate question sentence")

            if "blanks" not in result or not isinstance(result["blanks"], list):
                raise ValueError("Failed to generate blanks")

            blanks_list: List[BlankSlot] = []
            for i, blank_data in enumerate(result["blanks"]):
                if not isinstance(blank_data, dict):
                    continue
                blank_slot = BlankSlot(
                    index=blank_data.get("index", i),
                    placeholder=blank_data.get("placeholder", "[BLANK]"),
                    answer=blank_data.get("answer"),
                    hint=blank_data.get("hint")
                )
                blanks_list.append(blank_slot)

            blank_count = result["questionSentence"].count("[BLANK]")
            if blank_count != len(blanks_list):
                logger.warning(f"Blank count mismatch: {blank_count} in sentence vs {len(blanks_list)} in array")
                if blank_count > len(blanks_list):
                    for i in range(len(blanks_list), blank_count):
                        blanks_list.append(BlankSlot(index=i, placeholder="[BLANK]", answer=None, hint=None))
                else:
                    blanks_list = blanks_list[:blank_count]

            question_sentence = result["questionSentence"]
            original_sentence = result.get("originalSentence", "")
            if not original_sentence:
                sorted_blanks = sorted(blanks_list, key=lambda b: b.index)
                reconstructed = question_sentence
                for blank in sorted_blanks:
                    if blank.answer:
                        reconstructed = reconstructed.replace("[BLANK]", blank.answer, 1)
                original_sentence = reconstructed
                logger.info(f"Reconstructed original sentence: {original_sentence}")

            if "[BLANK]" in original_sentence:
                logger.warning(f"Warning: Some blanks were not properly filled. Original: {original_sentence}")

            return {
                "questionType": "Blank",
                "originalSentence": original_sentence,
                "questionSentence": question_sentence,
                "koreanSentence": result.get("koreanSentence", ""),
                "blanks": blanks_list,
                "difficulty": result.get("difficulty", difficulty),
                "topic": result.get("topic", topic)
            }

        except Exception as e:
            logger.error(f"Error generating blank quiz: {e}")
            return {
                "questionType": "Blank",
                "questionSentence": "I [BLANK] to school every day.",
                "koreanSentence": "나는 매일 학교에 [BLANK]요.",
                "blanks": [BlankSlot(index=0, placeholder="[BLANK]", answer="go", hint="이동하다")],
                "difficulty": difficulty,
                "topic": topic or "일상 대화"
            }
