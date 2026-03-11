# Egoeng LLM API 🚀

![Python badge](https://img.shields.io/badge/Python-3.11-blue?style=flat&logo=python&logoColor=white) ![FastAPI badge](https://img.shields.io/badge/FastAPI-0.115+-green?style=flat&logo=fastapi&logoColor=white) ![OpenAI badge](https://img.shields.io/badge/OpenAI-API-black?style=flat&logo=openai&logoColor=white)

## 📝 소개
**Egoeng LLM API**는 FastAPI 기반의 AI 학습 도우미 백엔드 서비스입니다.
OpenAI LLM을 활용하여 **퀴즈 생성**, **채팅**, **OCR 텍스트 추출** 등 다양한 교육용 API를 제공합니다.

### 🎯 주요 기능
- **퀴즈 생성**: 번역, 빈칸 채우기, 문장 배열 등 다양한 형태의 동적 퀴즈 생성
- **채팅 API**: 대화형 학습 지원
- **OCR 텍스트 추출**: 이미지에서 텍스트 인식 및 추출
- **Cloud Run 배포**: Docker 기반 클라우드 배포 지원





## 🗂️ APIs
자세한 API 스펙은 아래에서 확인할 수 있습니다.

### 주요 엔드포인트
- `POST /api/quiz/generate` - 퀴즈 생성
- `GET /api/quiz/{quiz_id}` - 퀴즈 조회  
- `POST /api/chat` - 채팅
- `POST /api/ocr/extract` - OCR 텍스트 추출 (상세)
- `POST /api/ocr/extract-simple` - OCR 텍스트 추출 (간단)
- `GET /health` - 헬스 체크





## ⚙ 기술 스택

### Back-end

![Python (for-the-badge)](https://img.shields.io/badge/Python-3.11-3776ab?style=for-the-badge&logo=python&logoColor=white)
![FastAPI (for-the-badge)](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![OpenAI (for-the-badge)](https://img.shields.io/badge/OpenAI-API-412991?style=for-the-badge&logo=openai&logoColor=white)
![Pydantic (for-the-badge)](https://img.shields.io/badge/Pydantic-v2-e92063?style=for-the-badge&logo=pydantic&logoColor=white)
![EasyOCR (for-the-badge)](https://img.shields.io/badge/EasyOCR-OCR-FF6B6B?style=for-the-badge)
![Pillow (for-the-badge)](https://img.shields.io/badge/Pillow-Image-3776ab?style=for-the-badge)

### DevOps & Deployment

![Docker (for-the-badge)](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Cloud Run (for-the-badge)](https://img.shields.io/badge/Google%20Cloud%20Run-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![python-dotenv (for-the-badge)](https://img.shields.io/badge/python--dotenv-Environment-3776ab?style=for-the-badge)




## 🛠️ 프로젝트 구조

```
egollm/
├── app/
│   ├── api/                      # API 라우터
│   │   ├── quiz_router.py        # 퀴즈 API
│   │   ├── chat_router.py        # 채팅 API
│   │   └── quiz_generator_router.py  # 퀴즈 생성 API
│   ├── core/                     # 핵심 설정
│   │   ├── config.py             # 설정 관리
│   │   └── llm_client.py         # LLM 클라이언트
│   ├── models/                   # 데이터 모델
│   │   ├── chat_models.py
│   │   ├── quiz_models.py
│   │   └── response_models.py
│   ├── services/                 # 비즈니스 로직
│   │   ├── quiz_service.py
│   │   ├── chat_service.py
│   │   ├── quiz_generator.py
│   │   ├── quiz_evaluator.py
│   │   └── generators/           # 퀴즈 생성기
│   ├── utils/                    # 유틸리티
│   │   ├── embedding_helper.py
│   │   └── text_splitter.py
│   └── main.py                   # FastAPI 앱 시작점
├── Dockerfile                    # Docker 설정
├── requirements.txt              # Python 의존성
├── API_SPEC.md                   # API 문서
├── OCR_API_SPEC.md              # OCR API 문서
└── README.md                     # 이 파일
```


## 🤔 기술적 이슈와 해결 과정


1) OpenAI(LLM) 호출
- 상황: 외부 API로서 모델 호출. 
- 문제: 응답 지연, rate limit(429), 가끔의 시간초과 발생.
- 해결: 비동기 호출과 재시도(backoff)/타임아웃 적용, 결과 캐시 및 배치 처리 권장.

2) 긴 텍스트(컨텍스트) 처리
- 상황: 사용자 입력 또는 문서가 토큰 한도를 초과 
- 문제: 한 번에 보내면 모델 입력 제한으로 실패하거나 비효율적 비용 발생.
- 해결: 의미 단위로 분할 후 요약 또는 선택 전송(선택적 컨텍스트 포함).

3) 퀴즈 생성의 안정성
- 상황: 모델 출력이 자유 형식이라 파싱이 불안정 
- 문제: 예상과 다른 포맷이 반환되면 파싱 오류로 서비스 실패 위험.
- 해결: Pydantic 스키마로 검증하고 실패 시 간단 포맷으로 재요청하거나 대체 흐름 적용.

4) OCR·이미지 처리(블로킹 작업)
- 상황: EasyOCR 등 이미지 처리 작업은 CPU 집약적이며 블로킹
- 문제: FastAPI 이벤트루프를 차단할 수 있어 응답 지연 발생.
- 해결: 이미지 전처리로 정확도 향상, 블로킹 작업은 스레드풀/별도 워커로 오프로드(또는 서비스 분리).

5) 배포 및 비밀(Secrets) 관리
- 상황: OpenAI 키 등 민감정보가 필요
- 문제: 환경변수 누락·노출 위험, 도커 이미지 크기·비용 문제.
- 해결: 환경변수/시크릿 매니저로 중앙관리, Docker 멀티스테이지로 이미지 최적화.
