import { useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import "../styles/design.css";
import logoUrl from "../data/ui/logo.png";

/** 목업 캔버스 크기 (1440×810). 창 크기에 맞춰 같은 비율로 줄입니다. */
const CANVAS_W = 1440;
const CANVAS_H = 810;

function fitCanvas(): { scale: number; x: number; y: number } {
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const scale = Math.min(1, vw / CANVAS_W, vh / CANVAS_H);
  return { scale, x: (vw - CANVAS_W * scale) / 2, y: (vh - CANVAS_H * scale) / 2 };
}

/** 목업 화면 한 장을 그대로 담는 틀. 안의 모든 규칙은 .dsg 아래에서만 적용됩니다. */
export function DesignFrame({ children, className = "" }: { children: ReactNode; className?: string }) {
  const [fit, setFit] = useState(fitCanvas);

  useEffect(() => {
    const onResize = () => setFit(fitCanvas());
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return (
    <div className="dsg-viewport">
      <div className={`dsg ${className}`} style={{ transform: `scale(${fit.scale})`, left: fit.x, top: fit.y }}>
        {children}
      </div>
    </div>
  );
}

/** 목업의 상단 바: 로고만 가운데에 둡니다. 뒤로 가기 링크는 실제 이동을 위해 왼쪽에 추가했습니다. */
export function DesignTopbar({ backTo, backLabel = "뒤로" }: { backTo?: string; backLabel?: string }) {
  return (
    <header className="topbar">
      {backTo && (
        <Link className="back" to={backTo}>
          ← {backLabel}
        </Link>
      )}
      <img className="brand" src={logoUrl} alt="PokéNav" />
    </header>
  );
}
