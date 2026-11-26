import { useState, type CSSProperties, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { useApi, type TrainerSummary } from "../../api/client";
import { DesignFrame, DesignTopbar } from "../../components/DesignFrame";
import { CHAMPION_ID, forVersion, TRAINER_IMAGE_BASE } from "../../config/trainerGroups";
import emblemPng from "../../data/plasma/plasma-emblem.png";
import emblemGif from "../../data/plasma/plasma-emblem.gif";

/**
 * 트레이너 정보 첫 화면: 관장 / 사천왕 및 챔피언 / 플라스마단 카드 3개 (포켓몬 블랙·화이트 분위기).
 * - 관장: 체육관마다 관장 1명(8명)과 몬스터볼. 마우스를 올리면 관장들이 숨쉬고(GIF), 몬스터볼이 잡을 때처럼 계속 흔들립니다.
 * - 사천왕 및 챔피언: 사천왕 4명 앞에 방 문의 파란 불빛(블랙·화이트 포켓몬리그에서 사천왕을 이기면 켜지는 불빛),
 *   뒤에 챔피언 노간주. 마우스를 올리면 파란 불이 차례로 켜지고 노간주 뒤로 금빛이 올라옵니다.
 * - 플라스마단: 엠블럼과 이름. 마우스를 올리면 카드가 커지며 엠블럼이 반짝이는 GIF로 자연스럽게 바뀝니다.
 * 마우스를 올린 효과는 키보드로 고를 때(포커스)도 같습니다.
 */

/** 체육관 순서대로 카드에 세울 관장 (1번은 세 쌍둥이 중 덴트, 8번은 고른 버전의 관장) */
const GYM_FACES: readonly string[] = ["cilan", "lenora", "burgh", "elesa", "clay", "skyla", "brycen", forVersion(["drayden", "iris"])[0]];

const ELITE_FACES: readonly string[] = ["shauntal", "grimsley", "caitlin", "marshal"];

/** 전신 그림(PNG)과 숨쉬기 GIF. 연무는 상세용으로 받은 GIF와 틀이 달라, 같은 틀로 만든 GIF를 씁니다. */
const pngOf = (id: string) => `${TRAINER_IMAGE_BASE}/${id}.png`;
const gifOf = (id: string) => `${TRAINER_IMAGE_BASE}/${id === "marshal" ? "marshal-idle" : id}.gif`;

/**
 * 인물 한 명: 평소에는 PNG, 카드에 마우스를 올리면 같은 자리의 숨쉬기 GIF로 서서히 바뀝니다.
 * (GIF는 84×84 칸에 그림이 2px 안쪽에 있어서, 84/80배로 키우고 2px만큼 당겨 PNG와 정확히 겹칩니다)
 * 그림 파일이 없으면(저장소에서 제외됨) PNG 자리에 이름 첫 글자 타일을 두고, GIF가 없으면 PNG(또는 타일)를 그대로 둡니다.
 */
function Sprite({ id, size, className = "" }: { id: string; size: number; className?: string }) {
  const [pngFailed, setPngFailed] = useState(false);
  const [gifFailed, setGifFailed] = useState(false);
  // 이름은 트레이너 목록 API에서 받습니다 (같은 주소는 한 번만 요청됩니다).
  const trainers = useApi<TrainerSummary[]>("/trainers");
  const name = trainers.status === "ok" ? trainers.data.find((t) => t.id === id)?.name ?? "" : "";
  return (
    <span className={`cat-sprite ${gifFailed ? "no-gif" : ""} ${className}`} style={{ "--s": `${size}px` } as CSSProperties}>
      {pngFailed ? (
        <span className="still cat-fallback" aria-hidden="true">
          {name.charAt(0)}
        </span>
      ) : (
        <img className="still" src={pngOf(id)} alt="" onError={() => setPngFailed(true)} />
      )}
      {!gifFailed && <img className="moving" src={gifOf(id)} alt="" onError={() => setGifFailed(true)} />}
    </span>
  );
}

function GymArt() {
  return (
    <div className="cat-art gym-art">
      {/* 몬스터볼: 마우스를 올리고 있는 동안 잡을 때처럼 흔들림 */}
      <div className="gym-ball" aria-hidden="true">
        <span className="ball">
          <span className="lid" />
          <span className="base" />
          <span className="btn" />
        </span>
      </div>
      <div className="gym-rows">
        {GYM_FACES.map((id) => (
          <Sprite key={id} id={id} size={76} />
        ))}
      </div>
    </div>
  );
}

function EliteArt() {
  return (
    <div className="cat-art elite-art">
      <div className="champ">
        <span className="aura" aria-hidden="true" />
        <Sprite id={CHAMPION_ID} size={128} />
      </div>
      <div className="elite-row">
        {ELITE_FACES.map((id, i) => (
          <div key={id} className="elite-slot" style={{ "--i": i } as CSSProperties}>
            <Sprite id={id} size={84} />
            <span className="door-light" aria-hidden="true" />
          </div>
        ))}
      </div>
    </div>
  );
}

function PlasmaArt() {
  return (
    <div className="cat-art plasma-art">
      <span className="emblem">
        <span className="glow" aria-hidden="true" />
        <img className="still" src={emblemPng} alt="" />
        <img className="moving" src={emblemGif} alt="" />
      </span>
    </div>
  );
}

const CATEGORIES: readonly { key: string; title: string; sub: string; path: string; art: ReactNode }[] = [
  { key: "gym", title: "관장", sub: "하나지방 체육관 8곳 · 배지 8개", path: "/trainers/gym", art: <GymArt /> },
  { key: "elite", title: "사천왕 및 챔피언", sub: "포켓몬리그 · 사천왕 4명과 챔피언", path: "/trainers/elite", art: <EliteArt /> },
  { key: "plasma", title: "플라스마단", sub: "게치스 · N", path: "/trainers/plasma", art: <PlasmaArt /> },
];

export function TrainerCategoryPage() {
  const navigate = useNavigate();

  return (
    <DesignFrame>
      <DesignTopbar backTo="/" backLabel="메인" />
      <div className="cat-page">
        <section className="panel cat-panel">
          <div className="ph">
            트레이너 정보<span className="sub">상대를 골라 파티와 상성을 확인하세요</span>
          </div>
          <div className="cat-stage">
            {CATEGORIES.map((c) => (
              <button key={c.key} type="button" className={`cat-card ${c.key}`} onClick={() => navigate(c.path)}>
                {c.art}
                <span className="cat-label">
                  <b>{c.title}</b>
                  <small>{c.sub}</small>
                </span>
              </button>
            ))}
          </div>
        </section>
      </div>
    </DesignFrame>
  );
}
