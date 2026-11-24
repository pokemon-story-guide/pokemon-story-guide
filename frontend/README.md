# Frontend

React + Vite + TypeScript로 만든 프론트엔드입니다.

## 실행 방법

```bash
cd frontend
npm install        # 처음 한 번, 라이브러리 바뀔 때
npm run dev        # http://localhost:5173
npm run build      # 타입 검사 후 배포용 빌드
```

화면의 포켓몬·장소·트레이너 정보는 백엔드 API에서 받으므로, **백엔드 서버를 먼저 켭니다** (`backend/api/README.md` 참고, 기본 http://127.0.0.1:8000).

- `/api/...` 요청은 Vite가 백엔드로 넘깁니다 (`vite.config.ts`의 proxy). 백엔드 주소가 다르면 환경 변수 `API_TARGET`으로 바꿉니다.
- 백엔드가 꺼져 있으면 각 화면에 "정보를 불러오지 못했어요" 오류 화면과 [다시 시도] 버튼이 나옵니다.

## 폴더 구조

```text
src/config/menuItems.ts   메인 메뉴 항목(이름, 설명, 경로) 정의
src/components/           공통 컴포넌트 (MenuList, ScreenFrame)
src/pages/                화면 단위 파일
src/styles/theme.css      디자인 토큰 (색, 글꼴, 간격). 디자인 확정 시 여기만 수정
src/styles/app.css        화면 구조 스타일 (토큰 변수만 사용)
src/assets/               로고, 배경 등 이미지 (디자인 확정 후 추가)
```

## 디자인 적용 방법

- 색, 글꼴, 간격은 `src/styles/theme.css`의 변수로만 관리합니다. 값을 바꾸면 전체 화면에 반영됩니다.
- 로고와 배경은 `src/pages/MainMenuPage.tsx`의 `main-menu__logo` 영역과 `theme.css`의 주석 위치에 연결합니다.

## 기능 화면 연결 방법

- 메뉴 이름과 경로는 `src/config/menuItems.ts`에서 관리합니다.
- 지금 기능 화면은 `PlaceholderPage`를 씁니다. 기능을 구현할 때는 `src/pages/`에 기능별 페이지를 만들고 `src/App.tsx`의 라우트에서 교체합니다.
- API 연결은 `src/api/`에 있습니다 (`client.ts`: 응답 타입·요청·`useApi`, `trainers.tsx`: 트레이너 목록 묶음).
- 백엔드 응답 모양이 바뀌면 `src/api/client.ts`의 타입부터 맞춥니다. 프론트에 데이터 복사본을 두지 않습니다.
