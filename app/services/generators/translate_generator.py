"""Translate quiz generator module.

Extracted from QuizGeneratorService.generate_translate_quiz to allow
independent testing and clearer separation of concerns.
"""

import json
import logging
from typing import Optional, Dict, Any
from app.services.llm_service import call_llm

logger = logging.getLogger(__name__)


class TranslateGenerator:
    @staticmethod
    def _parse_json_response(response: str) -> Dict[str, Any]:
        resp = response.strip()
        # JSON 코드 블록 제거
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
    def generate(difficulty: str = "intermediate", topic: Optional[str] = None, length: str = "short") -> Dict[str, Any]:
        try:
            prompt_parts = [
                "You are an English tutor creating translation quizzes for Korean learners.",
                f"Generate a {difficulty} level Korean sentence for translation practice.",
                "IMPORTANT: Create a DIFFERENT and VARIED sentence each time. Avoid repeating similar sentences.",
                "Use diverse topics, sentence structures, and vocabulary to ensure variety.",
            ]

            if topic:
                prompt_parts.append(f"Topic: {topic}")
            else:
                prompt_parts.append("Choose a random topic (daily conversation, hobbies, travel, work, food, weather, etc.)")

            if length == "short":
                prompt_parts.append("Keep it short (5-10 words in Korean).")
            elif length == "medium":
                prompt_parts.append("Keep it medium length (10-15 words in Korean).")
            else:
                prompt_parts.append("Keep it long (15-20 words in Korean).")

            prompt_parts.extend([
                "",
                "Return ONLY a JSON object with the following structure:",
                '{',
                '  "koreanSentence": "한국어 문장",',
                '  "hint": "힌트 (선택사항, 영어로)",',
                '  "difficulty": "beginner/intermediate/advanced",',
                '  "topic": "주제"',
                '}',
                "",
                "Do not include any explanation, only the JSON object."
            ])

            prompt = "\n".join(prompt_parts)
            response = call_llm(prompt, temperature=0.8)
            result = TranslateGenerator._parse_json_response(response)

            if "koreanSentence" not in result or not result["koreanSentence"]:
                raise ValueError("Failed to generate Korean sentence")

            result.setdefault("hint", None)
            result.setdefault("difficulty", difficulty)
            result.setdefault("topic", topic)
            result["questionType"] = "Translate"
            return result
        except Exception as e:
            logger.error(f"Error generating translate quiz: {e}")
            return {
                "questionType": "Translate",
                "koreanSentence": "안녕하세요, 오늘 날씨가 좋네요.",
                "hint": "Greeting and weather comment",
                "difficulty": difficulty,
                "topic": topic or "일상 대화"
            }
