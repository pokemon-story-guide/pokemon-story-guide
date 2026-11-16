import { useEffect, useRef, useState } from "react";
import { TRAINERS } from "../config/trainerData";
import { PORTRAIT_FORMAT, trainerImageSrc } from "../config/trainerGroups";

/**
 * 연출 전체 길이(ms). 시간 값은 app.css의 키프레임과 맞춰 둡니다.
 * 0~0.5초   번개 윗줄이 오른쪽 끝에서 왼쪽으로 펼쳐짐
 * 0.5~1.0초 번개 아랫줄이 펼쳐져 마름모가 생김
 * 1.0~1.26초 섬광
 * 1.26~2.46초 일반 띠와 사진 등장 후 유지 (사진은 1.7배까지 커짐)
 * 2.46~3.0초 퇴장: 더 커지면서 흐려짐 → 끝나면 상세 정보창
 */
export const INTRO_TOTAL_MS = 3000;

/** 띠 높이 = 사진 높이 (사진이 띠를 넘지 않도록 같은 높이로 맞춤) */
const BAND_H = 80;
const PHOTO_W = 160;

interface EliteIntroProps {
  id: string;
  onDone: () => void;
}

/** 고정된 난수(같은 모양이 항상 나오도록) */
function seeded(seed: number): () => number {
  let a = seed;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * 번개 줄을 윗줄과 아랫줄로 나눕니다.
 * 마름모 고리 하나마다 윗변(왼쪽→위→오른쪽)과 아랫변(오른쪽→아래→왼쪽)을 따로 만듭니다.
 * 윗줄이 먼저 펼쳐지고 아랫줄이 뒤따라 펼쳐져서 마름모가 완성됩니다.
 */
function boltEdges(): { top: string; bottom: string } {
  const rnd = seeded(11);
  const cy = 40;
  const baseL = 60;
  const baseH = 20;
  // 꼭짓점(고리와 고리가 만나는 점)을 먼저 정하고, 그 점의 높이를 양쪽 고리가 함께 씁니다.
  // 그래서 위줄과 아랫줄이 이어지는 자리에서 틈이 생기지 않습니다.
  const verts: { x: number; y: number }[] = [{ x: 1280, y: cy + (rnd() - 0.5) * 8 }];
  while (verts[verts.length - 1].x > 0) {
    const prev = verts[verts.length - 1];
    const L = baseL * (0.75 + rnd() * 0.5);
    verts.push({ x: Math.max(0, prev.x - L), y: cy + (rnd() - 0.5) * 8 });
  }
  const top: string[] = [];
  const bottom: string[] = [];
  for (let i = 0; i < verts.length - 1; i++) {
    const right = verts[i];
    const left = verts[i + 1];
    const h = baseH * (0.6 + rnd() * 0.75);
    const cx = (right.x + left.x) / 2;
    const yTop = cy - h + (rnd() - 0.5) * 6;
    const yBot = cy + h + (rnd() - 0.5) * 6;
    top.push(`M${left.x.toFixed(1)},${left.y.toFixed(1)} L${cx.toFixed(1)},${yTop.toFixed(1)} L${right.x.toFixed(1)},${right.y.toFixed(1)}`);
    bottom.push(`M${right.x.toFixed(1)},${right.y.toFixed(1)} L${cx.toFixed(1)},${yBot.toFixed(1)} L${left.x.toFixed(1)},${left.y.toFixed(1)}`);
  }
  return { top: top.join(" "), bottom: bottom.join(" ") };
}

/**
 * 사천왕 클릭 연출.
 * 띠와 사진은 하나의 묶음으로 등장하고, 사진만 커집니다. 이름은 띠 왼쪽 위 구석에 고정합니다.
 */
export function EliteIntro({ id, onDone }: EliteIntroProps) {
  const [failed, setFailed] = useState(false);
  // 부모가 다시 그려져도 타이머가 초기화되지 않도록 최신 콜백만 보관합니다.
  const doneRef = useRef(onDone);
  doneRef.current = onDone;
  const edges = boltEdges();

  useEffect(() => {
    const t = window.setTimeout(() => doneRef.current(), INTRO_TOTAL_MS);
    return () => window.clearTimeout(t);
  }, []);

  return (
    <>
      <div className="intro-dim" aria-hidden="true" />
      <div className="intro-flash" aria-hidden="true" />
      <div className="intro-stage" aria-hidden="true">
        <svg className="intro-bolt" viewBox="0 0 1280 80" preserveAspectRatio="none">
          <defs>
            {/* 윗줄: 오른쪽 끝에서 왼쪽으로 펼쳐짐 */}
            <clipPath id="bolt-clip-top">
              <rect className="bolt-reveal bolt-reveal-top" x="0" y="-20" width="1280" height="120" />
            </clipPath>
            {/* 아랫줄: 윗줄 다음에 펼쳐짐 */}
            <clipPath id="bolt-clip-bottom">
              <rect className="bolt-reveal bolt-reveal-bottom" x="0" y="-20" width="1280" height="120" />
            </clipPath>
          </defs>
          <g className="bolt-layer" clipPath="url(#bolt-clip-top)">
            <path className="bolt-blur" d={edges.top} />
            <path className="bolt-glow" d={edges.top} />
            <path className="bolt-core" d={edges.top} />
          </g>
          <g className="bolt-layer" clipPath="url(#bolt-clip-bottom)">
            <path className="bolt-blur" d={edges.bottom} />
            <path className="bolt-glow" d={edges.bottom} />
            <path className="bolt-core" d={edges.bottom} />
          </g>
        </svg>

        <div className="intro-group" style={{ height: BAND_H }}>
          <div className="intro-band" />
          <div className="intro-photo" style={{ width: PHOTO_W, height: BAND_H }}>
            {failed ? (
              <span className="intro-fallback">{TRAINERS[id].name.charAt(0)}</span>
            ) : (
              <img src={trainerImageSrc(id, PORTRAIT_FORMAT)} alt="" onError={() => setFailed(true)} />
            )}
          </div>
        </div>

        <span className="intro-name">{TRAINERS[id].name}</span>
      </div>
    </>
  );
}
