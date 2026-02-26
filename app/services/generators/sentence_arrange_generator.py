"""SentenceArrange generator extracted to its own module.

This file contains the logic to generate a SentenceArrange quiz. The
original implementation lived inside QuizGeneratorService; we extract it
so it can be unit-tested and reused independently.
"""

import logging
import random
from typing import Optional, Dict, Any
from app.services.llm_service import call_llm

logger = logging.getLogger(__name__)


class SentenceArrangeGenerator:
    @staticmethod
    def generate(difficulty: str = "intermediate", topic: Optional[str] = None, num_words: int = 5) -> Dict[str, Any]:
        """Generate a SentenceArrange quiz.

        Returns a dict matching the previous QuizGeneratorService contract for
        SentenceArrange so callers don't need to change.
        """
        try:
            num_words = max(3, min(10, num_words))

            prompt_parts = [
                "You are an English teacher creating sentence arrangement quizzes for Korean learners.",
                f"Generate a {difficulty} level English sentence with approximately {num_words} words.",
                "",
                "Requirements:",
                f"- The sentence must have exactly {num_words} words (count carefully)",
                "- Use natural, grammatically correct English",
                "- Make it appropriate for the difficulty level",
                "- Avoid contractions (e.g., use 'do not' instead of 'don't')",
                "- Avoid words that are too similar to each other (to prevent ambiguity)",
                "",
                "Output format - Return ONLY a JSON object:",
                '{',
                '  "sentence": "complete English sentence with exactly N words",',
                '  "koreanSentence": "Korean translation or hint",',
                '  "words": ["word1", "word2", ..., "wordN"]',
                '}',
                "",
                "IMPORTANT:",
                "- Count words CAREFULLY - must be exactly as specified",
                "- Do NOT include punctuation as separate words",
                "- words array must match sentence when joined by spaces",
            ]

            if topic:
                prompt_parts.insert(4, f"Topic: {topic}")

            prompt = "\n".join(prompt_parts)
            response = call_llm(prompt)

            # Reuse the simple JSON parsing from quiz_generator (caller can
            # still use QuizGeneratorService._parse_json_response if needed).
            # Here we do a minimal parse to keep this module independent.
            resp = response.strip()
            start = resp.find("{")
            end = resp.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON object found in LLM response for SentenceArrange")
            import json
            parsed = json.loads(resp[start:end])

            sentence = parsed.get("sentence", "").strip()
            korean = parsed.get("koreanSentence", "")
            words = parsed.get("words", [])

            if not sentence or not words:
                raise ValueError("Failed to generate sentence or words")

            if len(words) < 3 or len(words) > 10:
                raise ValueError(f"Generated word count {len(words)} not in range [3,10]")

            # Ensure words match sentence; fallback to simple split
            reconstructed = " ".join(words)
            if reconstructed.lower().replace(".", "") != sentence.lower().replace(".", ""):
                logger.warning(f"Word order mismatch: sentence='{sentence}' vs words='{reconstructed}'")
                words = sentence.replace(".", "").replace(",", "").split()

            shuffled_indices = list(range(len(words)))
            random.shuffle(shuffled_indices)
            shuffled_words = [words[i] for i in shuffled_indices]

            correct_order = [0] * len(words)
            for i, idx in enumerate(shuffled_indices):
                correct_order[idx] = i

            if sorted(correct_order) != list(range(len(words))):
                raise ValueError(f"Invalid correctOrder: {correct_order}")

            return {
                "questionType": "SentenceArrange",
                "question": sentence,
                "koreanSentence": korean,
                "words": words,
                "shuffledWords": shuffled_words,
                "correctOrder": correct_order,
                "difficulty": difficulty,
                "topic": topic
            }

        except Exception as e:
            logger.error(f"Error in SentenceArrangeGenerator: {e}")
            # Fallback minimal quiz
            words = ["The", "quick", "brown", "fox", "jumps"]
            shuffled_indices = list(range(len(words)))
            random.shuffle(shuffled_indices)
            shuffled_words = [words[i] for i in shuffled_indices]
            correct_order = [0] * len(words)
            for i, idx in enumerate(shuffled_indices):
                correct_order[idx] = i

            return {
                "questionType": "SentenceArrange",
                "question": "The quick brown fox jumps.",
                "koreanSentence": "재빠른 갈색 여우가 뛴다.",
                "words": words,
                "shuffledWords": shuffled_words,
                "correctOrder": correct_order,
                "difficulty": difficulty,
                "topic": topic or "일상"
            }
