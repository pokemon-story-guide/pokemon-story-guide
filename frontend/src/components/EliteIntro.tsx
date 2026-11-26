import { useEffect, useRef, useState } from "react";
import beamUrl from "../data/elite/elite-beam.gif";
import { trainerBustSrc } from "../config/trainerGroups";

/**
 * 사천왕 연출 전체 길이(ms). 게치스(플라스마단) 연출과 같은 순서입니다.
 * 0~300ms      검은 화면
 * 300~1500ms   노란 번개가 오른쪽에서 흘러 들어와 유지 (흐름 0.3초 + 유지 0.9초)
 * 1500~2500ms  번쩍임(1초), 마지막 섬광은 띠가 나올 때까지 밝게 유지
 * 2500ms~      금색 띠·사진·이름이 딜레이 없이 같은 순간 등장 → 1.7초 유지 후 끝
 */
export const INTRO_TOTAL_MS = 4200;

interface EliteIntroProps {
  id: string;
  /** 띠에 보여 줄 이름 (트레이너 API의 name) */
  name: string;
  /** "champion"이면 띠 색·번개는 사천왕과 같고, 사진·이름 위치만 게치스·N 연출처럼 (사진 왼쪽, 이름 띠 아래) */
  layout?: "elite" | "champion";
  onDone: () => void;
}

/** 사천왕 클릭 연출: 번개 → 번쩍임 → 띠·사진·이름. 띠 색과 사진·이름 위치는 기존 그대로입니다. */
export function EliteIntro({ id, name, layout = "elite", onDone }: EliteIntroProps) {
  // 0 검은 화면, 1 번개 흐름·유지, 2 번쩍임, 3 띠·사진·이름 등장
  const [phase, setPhase] = useState(0);
  // 마지막 섬광 전(2280ms) 번개를 숨깁니다. 띠는 2500ms에 딜레이 없이 나옵니다.
  const [boltOff, setBoltOff] = useState(false);
  const [failed, setFailed] = useState(false);
  // 부모가 다시 그려져도 타이머가 초기화되지 않도록 최신 콜백만 보관합니다.
  const doneRef = useRef(onDone);
  doneRef.current = onDone;

  useEffect(() => {
    const timers = [
      window.setTimeout(() => setPhase(1), 300),
      window.setTimeout(() => setPhase(2), 1500),
      window.setTimeout(() => setBoltOff(true), 2280),
      window.setTimeout(() => setPhase(3), 2500),
      window.setTimeout(() => doneRef.current(), INTRO_TOTAL_MS),
    ];
    return () => timers.forEach((t) => window.clearTimeout(t));
  }, []);

  return (
    <div className={layout === "champion" ? "elite-intro elite-intro--champion" : "elite-intro"} aria-hidden="true">
      {(phase === 1 || (phase === 2 && !boltOff)) && (
        <div className={`elite-intro__boltwrap${phase === 2 ? " is-flicker" : ""}`}>
          <img className="elite-intro__bolt" src={beamUrl} alt="" />
        </div>
      )}
      {phase === 2 && <div className="elite-intro__flash" />}
      <div className={`elite-intro__stage${phase >= 3 ? " is-band" : ""}`}>
        <div className="elite-intro__band" />
        <div className="elite-intro__photo">
          {failed ? (
            <span className="elite-intro__fallback">{name.charAt(0)}</span>
          ) : (
            <img src={trainerBustSrc(id)} alt="" onError={() => setFailed(true)} />
          )}
        </div>
        <span className="elite-intro__name">{name}</span>
      </div>
    </div>
  );
}
