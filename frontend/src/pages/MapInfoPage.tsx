import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { DesignFrame, DesignTopbar } from "../components/DesignFrame";
import { useApiAll, type LocationPokemon, type TrainerSummary } from "../api/client";
import { useTrainers } from "../api/trainers";
import { StatusView } from "../components/StatusView";
import { MAP_MOVES, MAP_STOPS, markerStyle, nodeHitStyle, type MapStop } from "../config/mapGraph";
import { GYM_CITIES, PORTRAIT_FORMAT, trainerImageSrc } from "../config/trainerGroups";
import { bwSpriteUrl, typeLabel } from "../lib/pokemon";
import mapUrl from "../data/ui/map-large.png";

type Direction = "left" | "right" | "up" | "down";

/** 처음 보여 줄 장소: 시작 마을인 마름꽃마을 */
const START_NAME = "마름꽃마을";

const STOP_BY_NAME = new Map(MAP_STOPS.map((s) => [s.name, s]));

/** 방향키 → 방향 */
const KEY_DIRECTION: Record<string, Direction> = {
  ArrowLeft: "left",
  ArrowRight: "right",
  ArrowUp: "up",
  ArrowDown: "down",
};

/** 방향 표시 (상단 안내와 위·아래 버튼에 씁니다) */
const DIRECTIONS: { dir: Direction; label: string; text: string }[] = [
  { dir: "left", label: "왼쪽", text: "◀" },
  { dir: "up", label: "위", text: "▲" },
  { dir: "down", label: "아래", text: "▼" },
  { dir: "right", label: "오른쪽", text: "▶" },
];

/** 장소 이름 바 오른쪽의 버튼은 위·아래만 둡니다. 왼쪽·오른쪽은 방향키로만 이동합니다. */
const BAR_BUTTONS = DIRECTIONS.filter((d) => d.dir === "up" || d.dir === "down");

/** 이동할 곳이 없으면 그 자리에 멈춥니다. */
const moveFrom = (name: string, dir: Direction) => MAP_MOVES[name]?.[dir] ?? name;

/** 출현 포켓몬 칸 수 */
const SLOTS = 6;

/** 시티 이름 → 체육관 번호(1~8). 체육관이 없는 장소는 undefined. */
function badgeOf(placeName: string): number | undefined {
  const index = GYM_CITIES.findIndex((c) => c.name === placeName);
  return index < 0 ? undefined : index + 1;
}

/** 사람 칸 한 줄 (관장, 사천왕, 챔피언 공통) */
function PersonRow({ t }: { t: TrainerSummary }) {
  return (
    <div className="lrow leader">
      <span className="face">
        <img src={trainerImageSrc(t.id, PORTRAIT_FORMAT)} alt="" />
      </span>
      <span className="nm">{t.name}</span>
      {t.type && <span className={`type ${t.type}`}>{typeLabel(t.type)}</span>}
    </div>
  );
}

/**
 * 맵 정보 화면.
 * - 방향키를 누르면 지도에 그려진 길 모양대로 움직입니다 (이동 표는 config/mapGraph.ts의 LINKS).
 * - 지도에는 선택한 장소의 원이 빨간색으로 바뀌며 깜빡입니다.
 * - 초록 점(꿈터·동굴 같은 특정 장소)도 가까운 도로·시티에서 방향키로 갈라져 들어가거나 눌러서 볼 수 있습니다.
 * - 도로·동굴은 오른쪽에 출현 포켓몬, 시티는 관장, 하나리그는 사천왕과 챔피언을 보여 줍니다.
 */
export function MapInfoPage() {
  const navigate = useNavigate();
  const [name, setName] = useState(STOP_BY_NAME.has(START_NAME) ? START_NAME : MAP_STOPS[0].name);
  const stop = STOP_BY_NAME.get(name) ?? MAP_STOPS[0];
  const moves = MAP_MOVES[stop.name] ?? {};

  const go = (dir: Direction) => setName((cur) => moveFrom(cur, dir));

  // 방향키: 지도의 길 모양대로 이동 (갈 곳이 없으면 멈춤)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const dir = KEY_DIRECTION[e.key];
      if (!dir) return;
      e.preventDefault();
      setName((cur) => moveFrom(cur, dir));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  /** 상단 안내: 갈 수 있는 방향만 보여 줍니다. */
  const hint = DIRECTIONS.filter((b) => moves[b.dir])
    .map((b) => `${b.text} ${moves[b.dir]}`)
    .join(" · ");


  return (
    <DesignFrame>
      <DesignTopbar backTo="/" backLabel="메인" />
      <div className="mapwrap">
        <section className="panel outer">
          <div className="ph">
            맵 정보
            <span className="sub">{hint} · 방향키로 이동</span>
          </div>
          <div className="pb">
            <div className="left">
              <div className="mapbox">
                <img src={mapUrl} alt="하나지방 지도" />
                <div className="dim" />
                {/* 마을·시티 원과 초록 점(특정 장소)을 누르면 그 장소로 이동합니다 */}
                {MAP_STOPS.filter((s) => s.kind !== "route").map((s) => (
                  <button
                    key={s.name}
                    type="button"
                    className={s.name === stop.name ? "mapcity on" : "mapcity"}
                    style={nodeHitStyle(s.px, s.py, s.kind === "town" ? 13 : 8)}
                    onClick={() => setName(s.name)}
                    aria-label={`${s.name} 보기`}
                    title={s.name}
                  />
                ))}
                {/* 현재 위치: 빨간 원만 장소를 따라 움직이며 깜빡입니다. 시티에서는 지도 속 원 안에 꼭 맞게 겹칩니다 */}
                <span
                  key={stop.name}
                  className="mapnode mapnode-red"
                  role="img"
                  aria-label={`현재 위치: ${stop.name}`}
                  style={markerStyle(stop.px, stop.py)}
                />
              </div>
              <div className="placebar">
                <span className="pname">{stop.name}</span>
                <span className="navgroup">
                  {BAR_BUTTONS.map((b) => (
                    <button
                      key={b.dir}
                      type="button"
                      className="navbtn"
                      onClick={() => go(b.dir)}
                      disabled={!moves[b.dir]}
                      aria-label={moves[b.dir] ? `${b.label}: ${moves[b.dir]}` : `${b.label}: 갈 곳 없음`}
                      title={moves[b.dir]}
                    >
                      {b.text}
                    </button>
                  ))}
                </span>
              </div>
            </div>

            {/* key: 장소를 옮기면 출현 목록 페이지를 처음으로 되돌립니다 */}
            <PlacePanel key={stop.id} stop={stop} onPokemon={(id) => navigate(`/pokemon/${id}`)} />
          </div>
        </section>
      </div>
    </DesignFrame>
  );
}

/**
 * 오른쪽 목록: 시티는 관장, 하나리그는 사천왕·챔피언(트레이너 API),
 * 도로·특정 장소는 출현 포켓몬(장소 API GET /api/locations/{id}/pokemon).
 */
function PlacePanel({ stop, onPokemon }: { stop: MapStop; onPokemon: (id: number) => void }) {
  const badge = badgeOf(stop.name);
  const isLeague = stop.name === "하나리그";
  const needsPeople = badge !== undefined || isLeague;
  const trainers = useTrainers();
  // 한 점에 장소가 둘이면(리조트데저트 + 고대의 성) 둘 다 불러와 합칩니다.
  const found = useApiAll<LocationPokemon[]>(needsPeople ? [] : stop.ids.map((id) => `/locations/${id}/pokemon`));
  const [page, setPage] = useState(0);

  if (needsPeople) {
    if (trainers.status !== "ok" || !trainers.groups) {
      return (
        <div className="list">
          <StatusView status={trainers.status === "ok" ? "loading" : trainers.status} what="트레이너" error={trainers.error} onRetry={trainers.retry} />
        </div>
      );
    }
    const people = badge !== undefined
      ? trainers.groups.gym(badge)
      : [...trainers.groups.eliteFour, ...(trainers.groups.champion ? [trainers.groups.champion] : [])];
    return (
      <div className="list">
        <div className="lh">
          {badge !== undefined ? `관장 · ${badge}번째 체육관` : "사천왕 · 챔피언"}
          <small>{people.length}명</small>
        </div>
        <div className="lbody">
          {people.map((t) => (
            <PersonRow key={t.id} t={t} />
          ))}
        </div>
      </div>
    );
  }

  if (found.status !== "ok") {
    return (
      <div className="list">
        <StatusView status={found.status} what="출현 포켓몬" error={found.error} onRetry={found.retry} />
      </div>
    );
  }
  const encounters = found.data.flat().filter((p, i, all) => all.findIndex((q) => q.id === p.id) === i);
  // 6마리씩 페이지로 나눠 보여 줍니다 (바람개비숲처럼 20마리인 곳도 모두 볼 수 있게).
  const pages = Math.max(1, Math.ceil(encounters.length / SLOTS));
  const cur = Math.min(page, pages - 1);
  const shown = encounters.slice(cur * SLOTS, cur * SLOTS + SLOTS);
  const blanks = Math.max(0, SLOTS - shown.length);
  return (
    <div className="list">
      <div className="lh">
        출현 포켓몬<small>{encounters.length}마리</small>
        {pages > 1 && (
          <span className="lpager">
            <button type="button" onClick={() => setPage(cur - 1)} disabled={cur === 0} aria-label="이전 출현 포켓몬">
              ◀
            </button>
            <span>
              {cur + 1}/{pages}
            </span>
            <button type="button" onClick={() => setPage(cur + 1)} disabled={cur === pages - 1} aria-label="다음 출현 포켓몬">
              ▶
            </button>
          </span>
        )}
      </div>
      <div className="lbody">
        {shown.map((p) => (
          <button key={p.id} type="button" className="lrow" onClick={() => onPokemon(p.id)}>
            <span className="mon">
              <img src={bwSpriteUrl(p.id)} alt="" />
            </span>
            <span className="nm">{p.name}</span>
            <span className="tp">{p.types.map((t) => typeLabel(t)).join(" · ")}</span>
          </button>
        ))}
        {Array.from({ length: blanks }, (_, i) => (
          <div key={`blank-${i}`} className="lrow blank" />
        ))}
        {encounters.length === 0 && <p className="empty">이 장소는 야생 포켓몬이 나오지 않거나 데이터가 없습니다.</p>}
      </div>
    </div>
  );
}
