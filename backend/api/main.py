from fastapi import FastAPI
from api.routers import health, trainers

app = FastAPI(title="포켓몬 스토리 공략 도우미 API")

# 서버 상태 확인용은 /api 밖에 둠
app.include_router(health.router)

# 기능 API는 prefix="/api"를 붙여서 연결
# 예: app.include_router(locations.router, prefix="/api")  → /api/locations
app.include_router(trainers.router, prefix="/api")