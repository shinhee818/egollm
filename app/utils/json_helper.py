from typing import List, Optional, Dict, Any
import json

@staticmethod
def _parse_json_response(response: str) -> Dict[str, Any]:
    """LLM 응답에서 JSON 파싱"""
    response = response.strip()

    # JSON 코드 블록 제거
    if "```json" in response:
        start = response.find("```json") + 7
        end = response.find("```", start)
        response = response[start:end].strip()
    elif "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        response = response[start:end].strip()

    # JSON 객체 찾기
    start = response.find("{")
    end = response.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("No JSON object found in response")

    json_str = response[start:end]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}, response: {response}")
        raise ValueError(f"Failed to parse JSON: {e}")



