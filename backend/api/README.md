# Backend API

## 실행 방법

```bash
cd backend
python3.12 -m venv .venv          # 처음 한 번만
source .venv/bin/activate         # 맥
.venv\Scripts\activate            # 윈도우
pip install -r requirements.txt   # 처음 한 번, 라이브러리 바뀔 때
uvicorn api.main:app --reload
```

- 아나콘다가 켜져 있으면(`(base)` 표시) 먼저 `conda deactivate`
- 헬스 체크: http://127.0.0.1:8000/health
- API 문서: http://127.0.0.1:8000/docs

## 폴더 구조

```
api/routers/    API 엔드포인트 (파일 하나 = 기능 묶음 하나)
api/schemas/    응답 데이터 모양 정의
api/services/   데이터 조회 (JSON, PokéAPI, Redis)
algorithm/      상성·추천 계산
ai/             LLM 연동
```

## API 추가하는 법

1. `api/routers/`에 파일을 만들고 `router = APIRouter(prefix="/기능이름", tags=["기능이름"])` 작성 (`health.py` 참고)
   - prefix에는 `/api` 제외 (예: `/locations`)
2. `api/main.py`에 `app.include_router(파일이름.router, prefix="/api")` 한 줄 추가
   - 최종 주소: `/api/기능이름`
   - `/health`는 서버 상태 확인용이라 `/api` 없이 연결

## 라이브러리 추가할 때

`pip install 라이브러리` 후 `pip freeze > requirements.txt`로 목록 갱신

## Docker로 실행

저장소 맨 위에서 실행 (Docker Desktop 실행 필요)

```bash
docker compose up --build   # 켜기
docker compose down         # 끄기
```

- API 문서: http://127.0.0.1:8000/docs
- Redis는 백엔드 컨테이너에서만 접근 (호스트 `redis`, 포트 `6379`)