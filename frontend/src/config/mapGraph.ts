import graphRaw from "../data/map/hana-graph.json";

/**
 * 하나지방 지도 데이터.
 * - 위치는 원본 지도(256×168)의 픽셀 좌표입니다. 마을·시티는 원의 중심, 도로는 노란 선의 가운데입니다.
 * - 화면에는 지도 대비 %로 바꿔서 씁니다.
 */

interface Graph {
  width: number;
  height: number;
  nodes: Record<string, [number, number]>;
  routes: Record<string, [number, number]>;
  /** 도로·마을이 아닌 특정 장소 (꿈터, 동굴 등) */
  places: Record<string, [number, number]>;
  /** 장소 이름 → 장소 ID (서버 장소 API의 id) */
  ids: Record<string, number>;
}

const GRAPH = graphRaw as unknown as Graph;

/** 지도 원본 크기 (px) */
export const MAP_WIDTH = GRAPH.width;
export const MAP_HEIGHT = GRAPH.height;

/**
 * 현재 위치 빨간 원의 지름 (원본 지도 px).
 * 화면용 큰 지도(map-large.png, 원본의 약 4.8배)에서 마을 원의 청록 속 + 속 테두리 지름(37px)과 같은 크기라,
 * 시티에서는 청록 부분을 빈틈없이 덮습니다.
 */
const NODE_SIZE = 37 / (1228 / 256);

/** 빨간 원을 지도 위치(원본 px)에 정확히 맞추는 스타일. 크기도 지도 대비 %라 지도 크기가 달라도 맞습니다. */
export function markerStyle(px: number, py: number) {
  return {
    left: `${((px - NODE_SIZE / 2) / MAP_WIDTH) * 100}%`,
    top: `${((py - NODE_SIZE / 2) / MAP_HEIGHT) * 100}%`,
    width: `${(NODE_SIZE / MAP_WIDTH) * 100}%`,
    height: `${(NODE_SIZE / MAP_HEIGHT) * 100}%`,
  };
}

/** 지도 위 원·점을 누를 수 있게 놓는 칸의 스타일 (size: 원본 px 지름) */
export function nodeHitStyle(px: number, py: number, size = 13) {
  return {
    left: `${((px - size / 2) / MAP_WIDTH) * 100}%`,
    top: `${((py - size / 2) / MAP_HEIGHT) * 100}%`,
    width: `${(size / MAP_WIDTH) * 100}%`,
    height: `${(size / MAP_HEIGHT) * 100}%`,
  };
}

type Direction = "left" | "right" | "up" | "down";

const OPPOSITE: Record<Direction, Direction> = { left: "right", right: "left", up: "down", down: "up" };

/**
 * 방향키 이동: 지도에 그려진 길 모양대로 움직입니다. (사용자가 지도에 그린 화살표 기준)
 * [A, 방향, B] = A에서 그 방향키를 누르면 B로 가고, B에서 반대 방향키를 누르면 A로 돌아옵니다.
 * - 가로 길은 ← →, 세로 길은 ↑ ↓, 비스듬한 길은 ← → 와 ↑ ↓ 둘 다 됩니다.
 * - 한 곳에서 같은 방향으로 갈 길이 둘이면 뒤에 적은 줄이 이깁니다.
 *   (궐수시티 → 는 7번도로, 물결마을 ← 는 14번도로. 반대쪽 길은 ↓ / ↑ 로 갑니다)
 */
const LINKS: readonly [string, readonly Direction[], string][] = [
  ["마름꽃마을", ["up"], "1번도로"],
  ["1번도로", ["up"], "넝쿨마을"],
  ["넝쿨마을", ["up"], "2번도로"],
  ["2번도로", ["up"], "성신시티"],
  ["성신시티", ["left"], "3번도로"],
  ["3번도로", ["left"], "칠보시티"],
  ["칠보시티", ["left"], "구름시티"],
  ["구름시티", ["up"], "4번도로"],
  ["4번도로", ["up"], "뇌문시티"],
  ["4번도로", ["left"], "16번도로"],
  ["뇌문시티", ["left"], "5번도로"],
  ["5번도로", ["left"], "물풍경도개교"],
  ["물풍경도개교", ["left"], "물풍경시티"],
  ["물풍경시티", ["left", "up"], "6번도로"],
  ["6번도로", ["left", "up"], "궐수시티"],
  ["궐수시티", ["right", "up"], "7번도로"],
  ["7번도로", ["right", "up"], "8번도로"],
  ["8번도로", ["right", "up"], "설화시티"],
  ["설화시티", ["right"], "9번도로"],
  ["9번도로", ["right"], "쌍용시티"],
  ["쌍용시티", ["up"], "10번도로"],
  ["10번도로", ["up", "right"], "챔피언로드"],
  ["챔피언로드", ["up", "right"], "하나리그"],
  ["쌍용시티", ["right"], "11번도로"],
  ["11번도로", ["right"], "빌리지브리지"],
  ["빌리지브리지", ["right"], "12번도로"],
  ["12번도로", ["right"], "보배마을"],
  ["보배마을", ["right", "down"], "13번도로"],
  ["13번도로", ["right", "down"], "물결마을"],
  ["물결마을", ["left", "down"], "14번도로"],
  ["14번도로", ["left", "down"], "블랙시티"],
  ["블랙시티", ["left"], "15번도로"],
  ["15번도로", ["left"], "뇌문시티"],
  ["마름꽃마을", ["left"], "17번수로"],

  // 초록 점(특정 장소): 가까운 도로·시티에서 점이 있는 방향으로 갈라집니다.
  // 같은 방향의 기존 길을 덮어쓰는 곳은 그 길을 다른 방향키로 갈 수 있습니다 (괄호 안).
  ["성신시티", ["right"], "꿈터"],
  ["3번도로", ["up"], "지하수맥굴"],
  ["칠보시티", ["down"], "바람개비숲(사색의들판)"],
  ["16번도로", ["left"], "리조트데저트"],
  ["뇌문시티", ["up"], "미혹의 숲"],
  ["물풍경시티", ["down"], "냉동컨테이너"],
  ["물풍경시티", ["up"], "궐수의동굴(길잡이의공간)"], // (6번도로는 ←)
  ["6번도로", ["left"], "전기돌동굴"], // (궐수시티는 ↑)
  ["8번도로", ["left"], "타워오브해븐"], // (7번도로는 ↓)
  ["8번도로", ["right"], "태엽산"], // (설화시티는 ↑)
  ["설화시티", ["up"], "용나선탑"],
  ["9번도로", ["up"], "설화의 습지초원"],
  ["보배마을", ["up"], "자이언트홀"],
  ["물결마을", ["right"], "물결만"],
  ["14번도로", ["left"], "풍요의 사당"], // (블랙시티는 ↓)
  ["17번수로", ["up"], "P2랩"],
  ["구름시티", ["down"], "리버티가든섬"],
];

/** 한 점에 장소가 둘 이상 있는 곳: 오른쪽 목록에 함께 보여 줍니다 (고대의 성은 리조트데저트 안) */
const MERGED_PLACES: Record<string, string[]> = {
  리조트데저트: ["고대의 성"],
};

/** 한쪽으로만 가는 이동 (10번도로에서 ← 를 눌러도 쌍용시티로 내려옵니다) */
const ONE_WAY: readonly [string, Direction, string][] = [["10번도로", "left", "쌍용시티"]];

export interface MapStop {
  /** 장소 ID (서버 장소 API의 id) */
  id: number;
  /** 이 점에 함께 있는 장소 번호 전부 (보통 id 하나) */
  ids: number[];
  /** 화면에 보이는 이름 */
  name: string;
  /** town: 마을·시티 원, route: 도로, spot: 초록 점(특정 장소)·다리 */
  kind: "town" | "route" | "spot";
  /** 지도 위 위치 (%) */
  x: number;
  y: number;
  /** 지도 위 위치 (원본 지도 px) */
  px: number;
  py: number;
}

function placeIdOf(name: string): number | undefined {
  return GRAPH.ids[name];
}

function stopOf(name: string): MapStop | undefined {
  const id = placeIdOf(name);
  const isRoute = /번(도로|수로)$/.test(name);
  const spot = !isRoute && !GRAPH.nodes[name];
  const pos = isRoute ? GRAPH.routes[name] : GRAPH.nodes[name] ?? GRAPH.places[name];
  if (id === undefined || !pos) return undefined;
  const extra = (MERGED_PLACES[name] ?? []).map(placeIdOf).filter((v): v is number => v !== undefined);
  return {
    id,
    ids: [id, ...extra],
    name,
    kind: isRoute ? "route" : spot ? "spot" : "town",
    px: pos[0],
    py: pos[1],
    x: (pos[0] / MAP_WIDTH) * 100,
    y: (pos[1] / MAP_HEIGHT) * 100,
  };
}

/** 지도에 표시하는 장소들 */
export const MAP_STOPS: MapStop[] = [...new Set(LINKS.flatMap(([a, , b]) => [a, b]))]
  .map(stopOf)
  .filter((s): s is MapStop => s !== undefined);

/** 장소 이름 → 방향별로 이동할 장소 이름 (지도에 없는 장소는 뺍니다) */
export const MAP_MOVES: Record<string, Partial<Record<Direction, string>>> = (() => {
  const known = new Set(MAP_STOPS.map((s) => s.name));
  const moves: Record<string, Partial<Record<Direction, string>>> = {};
  const set = (from: string, dir: Direction, to: string) => {
    if (known.has(from) && known.has(to)) moves[from] = { ...moves[from], [dir]: to };
  };
  LINKS.forEach(([a, dirs, b]) =>
    dirs.forEach((dir) => {
      set(a, dir, b);
      set(b, OPPOSITE[dir], a);
    }),
  );
  ONE_WAY.forEach(([a, dir, b]) => set(a, dir, b));
  return moves;
})();

/** 장소 ID로 방향키 이동 장소를 찾습니다. 없으면 undefined. */
export function stopByPlaceId(placeId: number): MapStop | undefined {
  return MAP_STOPS.find((s) => s.id === placeId);
}

/** 장소 ID → 지도 위 이름 */
const NAME_BY_ID: Record<number, string> = Object.fromEntries(Object.entries(GRAPH.ids).map(([name, id]) => [id, name]));

/**
 * 장소 ID(서버 장소 API의 id)로 지도 위 위치(원본 px)를 찾습니다.
 * 마을·시티, 도로에 더해 꿈터·동굴 같은 특정 장소도 찾습니다. 지도에 없으면 undefined.
 */
export function placePosition(placeId: number): { px: number; py: number } | undefined {
  const name = NAME_BY_ID[placeId];
  if (name === undefined) return undefined;
  const pos = GRAPH.nodes[name] ?? GRAPH.routes[name] ?? GRAPH.places[name];
  return pos ? { px: pos[0], py: pos[1] } : undefined;
}
