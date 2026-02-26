import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Generator

load_dotenv()

def call_llm(prompt: str, temperature: float = 0.3) -> str:
    """공통 LLM 호출
    
    Args:
        prompt: 프롬프트
        temperature: 생성 다양성 (0.0-2.0). 높을수록 다양함. 기본값 0.3
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable")

    client = OpenAI(api_key=api_key)
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an English tutor helping Korean learners."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return "(LLM request failed)"

def call_llm_stream(prompt: str, temperature: float = 0.7) -> Generator[str, None, None]:
    """
    OpenAI 스트리밍 호출
    
    Args:
        prompt: 프롬프트
        temperature: 생성 다양성
    
    Yields:
        각 청크 문자열
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable")
    
    client = OpenAI(api_key=api_key)
    
    try:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an English tutor helping Korean learners."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            stream=True  # 스트리밍 활성화
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        print(f"[LLM STREAM ERROR] {e}")
        yield f"(Stream failed: {str(e)})"
