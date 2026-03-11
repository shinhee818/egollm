<div align="center">

<!-- logo -->
<!-- <img src="https://user-images.githubusercontent.com/80824750/208554611-f8277015-12e8-48d2-b2cc-d09d67f03c02.png" width="300"/> -->

# Egoeng LLM API 🚀

[<img src="https://img.shields.io/badge/Python-3.11-blue?style=flat&logo=python&logoColor=white" />]() [<img src="https://img.shields.io/badge/FastAPI-0.115+-green?style=flat&logo=fastapi&logoColor=white" />]() [<img src="https://img.shields.io/badge/OpenAI-API-black?style=flat&logo=openai&logoColor=white" />]()

</div> 

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
<div>
<img src="https://img.shields.io/badge/Python-3.11-3776ab?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
<img src="https://img.shields.io/badge/OpenAI-API-412991?style=for-the-badge&logo=openai&logoColor=white" />
<img src="https://img.shields.io/badge/Pydantic-v2-e92063?style=for-the-badge&logo=pydantic&logoColor=white" />
<img src="https://img.shields.io/badge/EasyOCR-OCR-FF6B6B?style=for-the-badge" />
<img src="https://img.shields.io/badge/Pillow-Image-3776ab?style=for-the-badge" />
</div>

### DevOps & Deployment
<div>
<img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
<img src="https://img.shields.io/badge/Google%20Cloud%20Run-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white" />
<img src="https://img.shields.io/badge/python--dotenv-Environment-3776ab?style=for-the-badge" />
</div>




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

### 1. OCR 인식 정확도 개선
**이슈:** EasyOCR의 낮은 인식률로 인한 사용자 불만
- **해결:** 이미지 전처리 파이프라인 구현
- 이미지 명도 조정, 노이즈 제거, 해상도 향상
- 다양한 이미지 형식 및 언어 지원 추가

### 2. 동시성 처리 문제
**이슈:** 다중 사용자 동시 요청 시 응답 지연
- **해결:** FastAPI의 비동기 처리 활용
- 데이터베이스 연결 풀링 구현
- 요청 큐 및 워커 스레드 관리

### 3. 퀴즈 생성 다양성
**이슈:** 반복적인 패턴의 퀴즈 생성
- **해결:** 프롬프트 엔지니어링 및 LLM 파라미터 조정
- temperature 값을 조정하여 창의성과 일관성 균형
- 다양한 주제 및 난이도별 전문 프롬프트 개발

### 4. 배포 환경 설정
**이슈:** 로컬과 클라우드 환경 간의 설정 차이
- **해결:** python-dotenv를 활용한 환경 변수 관리
- Docker 레이어 캐싱 최적화로 배포 시간 단축
- Cloud Run 서버리스 아키텍처 구축


 
