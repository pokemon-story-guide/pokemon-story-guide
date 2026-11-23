import { ScreenFrame } from "../components/ScreenFrame";

interface PlaceholderPageProps {
  title: string;
}

/**
 * 아직 API와 연결하지 않은 기능 화면의 자리표시자.
 * 기능을 구현할 때 이 파일 대신 각 기능의 페이지 파일을 만들어 교체합니다.
 */
export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <ScreenFrame title={title}>
      <p className="placeholder">준비 중인 화면입니다.</p>
    </ScreenFrame>
  );
}
