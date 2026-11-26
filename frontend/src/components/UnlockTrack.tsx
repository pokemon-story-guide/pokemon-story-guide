import { useEffect, useRef } from "react";

/** 공이 왼쪽 끝에서 오른쪽 끝까지 굴러가는 시간 (ms). CSS의 --travel과 같은 값입니다. */
export const UNLOCK_TRAVEL_MS = 1600;

/**
 * 잠금 해제 진행 바 (유튜브 재생바처럼).
 * - 몬스터볼이 왼쪽에서 오른쪽으로 굴러가고, 지나간 자리는 빨갛게 채워집니다.
 * - progress(0~1)가 바뀌면 공이 그 위치까지 굴러갑니다. 오른쪽 끝(1)에 닿으면 onArrive를 부릅니다.
 *   (예: 사천왕 화면에서 오른쪽 끝에 닿으면 챔피언이 열림)
 */
export function UnlockTrack({ progress, onArrive, label }: { progress: number; onArrive?: () => void; label?: string }) {
  const arrived = progress >= 1;
  const doneRef = useRef(onArrive);
  doneRef.current = onArrive;

  useEffect(() => {
    if (!arrived) return;
    const t = window.setTimeout(() => doneRef.current?.(), UNLOCK_TRAVEL_MS);
    return () => window.clearTimeout(t);
  }, [arrived]);

  const p = Math.min(Math.max(progress, 0), 1);
  return (
    <div className={arrived ? "unlock-track arrived" : "unlock-track"} role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(p * 100)} aria-label={label}>
      <div className="ut-rail">
        <div className="ut-fill" style={{ width: `${p * 100}%` }} />
      </div>
      <span className="ut-ball" style={{ left: `${p * 100}%`, transform: `translate(-50%, -50%) rotate(${p * 720}deg)` }} aria-hidden="true" />
    </div>
  );
}
