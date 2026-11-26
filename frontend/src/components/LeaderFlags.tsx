import { useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { PORTRAIT_FORMAT, trainerImageSrc } from "../config/trainerGroups";

/**
 * 상대 선택 패널 (배틀 VS 패널 디자인). 관장·사천왕·챔피언·플라스마단 화면이 함께 씁니다.
 * - 비스듬하게 기운 타입 색 패널에 인물 사진과 이름이 들어갑니다.
 * - 열린 패널만 인물이 보이고, 잠긴 패널은 회색 + 그림자입니다.
 * - 사진 칸은 정사각형이라 전신 그림(80×80)이 크게 보입니다. 여러 명이면(관장 1·8번) 조금 작은 정사각형 칸을 위아래로 쌓고,
 *   패널 기울기를 따라 옆으로 옮겨서 패널 밖으로 잘리지 않게 합니다.
 *
 * 패널 크기 (그룹별)
 * - 관장 8칸: 138×560, 사진 1배
 * - 사천왕 4명: 왼쪽 구역 160×560, 사진 1.15배 (연무 전신이 147px로 보이는 크기)
 * - 챔피언 1명: 오른쪽 구역 330×590, 사진 2배 (사천왕 구역과의 사이에 잠금 해제 진행 바)
 * - 플라스마단 2명: 300×570, 사진 1.9배
 */
export type FlagGroup = "gym" | "elite" | "champion" | "plasma";

const GROUP_STYLE: Record<FlagGroup, { w: number; h: number; ps: number }> = {
  gym: { w: 138, h: 560, ps: 1 },
  elite: { w: 160, h: 560, ps: 1.15 },
  champion: { w: 330, h: 590, ps: 2 },
  plasma: { w: 300, h: 570, ps: 1.9 },
};

export interface FlagPerson {
  id: string;
  name: string;
}

export interface FlagItem {
  key: string;
  color: string;
  people: FlagPerson[];
  locked?: boolean;
  /** 이름 아래 작은 글씨 (예: 타입, 시티 이름) */
  sub?: string;
}

function Face({ id, name }: { id: string; name: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return <span className="dsg-face-fallback" aria-hidden="true">{name.charAt(0)}</span>;
  }
  return <img src={trainerImageSrc(id, PORTRAIT_FORMAT)} alt="" onError={() => setFailed(true)} />;
}

interface Props {
  group: FlagGroup;
  flags: readonly FlagItem[];
  /** 있으면 화면을 두 구역으로 나눠 오른쪽에 따로 둡니다 (예: 사천왕 왼쪽, 챔피언 오른쪽). between은 두 구역 사이에 놓입니다 (예: 잠금 해제 진행 바). */
  aside?: { group: FlagGroup; flags: readonly FlagItem[]; between?: ReactNode };
  onPick: (person: FlagPerson, flag: FlagItem) => void;
}

/** 패널 기울기 (CSS의 skewX(-10deg)와 같은 값) */
const SLANT = Math.tan((10 * Math.PI) / 180);

export function LeaderFlags({ group, flags, aside, onPick }: Props) {
  const [hoverKey, setHoverKey] = useState<string | null>(null);
  const stageRef = useRef<HTMLDivElement>(null);

  // 패널이 기울어 있어서, 위쪽 인물은 오른쪽·아래쪽 인물은 왼쪽으로 옮겨 패널 가운데선을 따라가게 합니다
  // (한 패널에 3명인 1번 체육관처럼 위아래 끝에 있는 그림이 패널 밖으로 잘리지 않게).
  useLayoutEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    stage.querySelectorAll<HTMLElement>(".vsp-in").forEach((box) => {
      const mid = box.clientHeight / 2;
      box.querySelectorAll<HTMLElement>(".person, .sub").forEach((el) => {
        const dy = el.offsetTop + el.offsetHeight / 2 - mid;
        el.style.transform = `translateX(${(-dy * SLANT).toFixed(1)}px)`;
      });
    });
  });

  const renderPanels = (list: readonly FlagItem[], style: { w: number; h: number; ps: number }) =>
    list.map((flag) => {
      const selected = hoverKey === flag.key && !flag.locked;
      const single = flag.people.length === 1;
      const cssVars = {
        "--c": flag.color,
        "--fw": `${style.w}px`,
        "--fh": `${style.h}px`,
        "--ps": style.ps,
      } as CSSProperties;
      const classes = ["vsp"];
      if (selected) classes.push("sel");
      if (flag.locked) classes.push("locked");
      if (single) classes.push("single");
      return (
        <div
          key={flag.key}
          className={classes.join(" ")}
          style={cssVars}
          onMouseEnter={() => setHoverKey(flag.key)}
          onMouseLeave={() => setHoverKey(null)}
        >
          <div className="vsp-in">
            {flag.people.map((person) => (
              <button
                key={person.id}
                type="button"
                className={flag.locked ? "person shadow" : "person"}
                aria-label={flag.locked ? `${person.name} (잠김)` : person.name}
                aria-disabled={flag.locked}
                onClick={() => {
                  if (!flag.locked) onPick(person, flag);
                }}
              >
                <span className="vph">
                  <Face id={person.id} name={person.name} />
                </span>
                <span className="nm">{person.name}</span>
              </button>
            ))}
            {flag.sub && <span className="sub">{flag.sub}</span>}
          </div>
        </div>
      );
    });

  if (aside) {
    return (
      <div className="flag-stage split" ref={stageRef}>
        <div className="flag-zone main">{renderPanels(flags, GROUP_STYLE[group])}</div>
        {aside.between && <div className="flag-between">{aside.between}</div>}
        <div className="flag-zone side">{renderPanels(aside.flags, GROUP_STYLE[aside.group])}</div>
      </div>
    );
  }
  return (
    <div className="flag-stage" ref={stageRef}>
      {renderPanels(flags, GROUP_STYLE[group])}
    </div>
  );
}
