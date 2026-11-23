import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface ScreenFrameProps {
  title: string;
  /** 상위 화면 경로. 있으면 "뒤로" 링크를 보여 줍니다. */
  backTo?: string;
  /** 상단 경로 표시 (예: 관장별 > 성신시티). 없으면 표시하지 않습니다. */
  breadcrumb?: string;
  children: ReactNode;
}

/**
 * 모든 화면의 공통 틀 (제목, 뒤로 가기, 메인으로).
 * 로고나 배경을 넣을 자리는 header와 main 안에 있습니다.
 */
export function ScreenFrame({ title, backTo, breadcrumb, children }: ScreenFrameProps) {
  return (
    <div className="screen">
      <header className="screen__header">
        {breadcrumb && <p className="screen__breadcrumb">{breadcrumb}</p>}
        <h1 className="screen__title">{title}</h1>
      </header>
      <main className="screen__body">{children}</main>
      <footer className="screen__footer">
        {backTo && (
          <Link to={backTo} className="back-link">
            뒤로
          </Link>
        )}
        <Link to="/" className="back-link">
          메인으로
        </Link>
      </footer>
    </div>
  );
}
