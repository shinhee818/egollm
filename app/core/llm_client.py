# -------------------------------------------------------
# 공통 LLM 호출 함수
# -------------------------------------------------------
def call_llm(prompt: str, temperature: float = 0.3) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable")

    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an English tutor helping Korean learners."},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return completion.choices[0].message.content.strip()