# Egoeng LLM API 🚀

![Python badge](https://img.shields.io/badge/Python-3.11-blue?style=flat&logo=python&logoColor=white) ![FastAPI badge](https://img.shields.io/badge/FastAPI-0.115+-green?style=flat&logo=fastapi&logoColor=white) ![OpenAI badge](https://img.shields.io/badge/OpenAI-API-black?style=flat&logo=openai&logoColor=white)

## 📝 소개
**Egoeng LLM API**는 FastAPI 기반의 AI 학습 도우미 백엔드 서비스입니다.
OpenAI LLM을 활용하여 **퀴즈 생성**, **채팅** 등 다양한 교육용 API를 제공합니다.

### 🎯 주요 기능
- **퀴즈 생성**: 번역, 빈칸 채우기, 문장 배열 등 다양한 형태의 동적 퀴즈 생성
- **채팅 API**: 대화형 학습 지원
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

