# Frontend

React + Vite + TypeScript로 만든 프론트엔드입니다.

## 실행 방법

```bash
cd frontend
npm install        # 처음 한 번, 라이브러리 바뀔 때
npm run dev        # http://localhost:5173
npm run build      # 타입 검사 후 배포용 빌드
```

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
- API 주소와 프록시 설정은 서버 연결 방식이 정해진 뒤 `vite.config.ts`와 설정 파일에 추가합니다.
