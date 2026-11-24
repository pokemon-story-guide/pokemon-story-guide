import { useEffect, useRef, useState } from "react";
import bandUrl from "../../data/plasma/plasma-band.png";
import boltUrl from "../../data/plasma/plasma-bolt.gif";
import emblemUrl from "../../data/plasma/plasma-emblem.gif";
import ghetsisUrl from "../../data/plasma/plasma-ghetsis.png";
import nUrl from "../../data/plasma/plasma-n.png";

/** 연출에 나오는 플라스마단 인물. 사진은 띠 높이에 맞춰 원래 비율로 보입니다. */
const PEOPLE = {
  ghetsis: { name: "게치스", src: ghetsisUrl, ratio: "126 / 64" },
  n: { name: "N", src: nUrl, ratio: "128 / 64" },
} as const;

export type PlasmaPerson = keyof typeof PEOPLE;

/**
 * 타이밍: 검은 화면 0.3초 → 전기 1.2초(흐름 0.3초 + 유지 0.9초, 300~1500ms)
 *          → 번개가 1초 찌릿찌릿 섬광(1500~2500ms, 마지막 섬광은 띠가 나올 때까지 밝게 유지) → 띠·문양·게치스·이름이 밝게 튀며 등장 → 1.7초 유지 뒤 끝.
 */
export const PLASMA_INTRO_MS = 4200;

interface PlasmaIntroProps {
  /** 누구의 연출인지 (기본: 게치스) */
  who?: PlasmaPerson;
  onDone: () => void;
}

/**
 * 플라스마단 연출 (게치스, N 공통): 검은 화면 → 전기 GIF → 섬광 → 섬광 후 띠·움직이는 문양·인물 PNG·이름이 한꺼번에 등장 → 상세로 이동.
 * 띠 아래선은 고정, 인물 PNG는 위로만 튀어나오고 아래로는 넘지 않습니다.
 */
export function PlasmaIntro({ who = "ghetsis", onDone }: PlasmaIntroProps) {
  const person = PEOPLE[who];
  // 0 검은 화면, 1 전기 GIF 흐름·유지, 2 번쩍임, 3 띠·문양·게치스·이름 등장
  const [phase, setPhase] = useState(0);
  // 마지막 섬광 전(2280ms) 번개를 숨깁니다. 띠는 2500ms에 딜레이 없이 나옵니다.
  const [boltOff, setBoltOff] = useState(false);
  // 부모가 다시 그려져도 타이머가 초기화되지 않도록 최신 콜백만 보관합니다.
  const doneRef = useRef(onDone);
  doneRef.current = onDone;

  useEffect(() => {
    const timers = [
      window.setTimeout(() => setPhase(1), 300),
      window.setTimeout(() => setPhase(2), 1500),
      window.setTimeout(() => setBoltOff(true), 2280),
      window.setTimeout(() => setPhase(3), 2500),
      window.setTimeout(() => doneRef.current(), PLASMA_INTRO_MS),
    ];
    return () => timers.forEach((t) => window.clearTimeout(t));
  }, []);

  return (
    <div className="plasma-intro" aria-hidden="true">
      {(phase === 1 || (phase === 2 && !boltOff)) && (
        <div className={`plasma-intro__boltwrap${phase === 2 ? " is-flicker" : ""}`}>
          <img className="plasma-intro__bolt" src={boltUrl} alt="" />
        </div>
      )}
      {phase === 2 && <div className="plasma-intro__flash" />}
      <div className={`plasma-intro__stage${phase >= 3 ? " is-band" : ""}`}>
        <div className="plasma-intro__band">
          <img className="plasma-intro__bandimg" src={bandUrl} alt="" />
        </div>
        <img className="plasma-intro__emblem" src={emblemUrl} alt="" />
        <img className="plasma-intro__portrait" src={person.src} alt="" style={{ aspectRatio: person.ratio }} />
        <p className="plasma-intro__name">{person.name}</p>
      </div>
    </div>
  );
}
