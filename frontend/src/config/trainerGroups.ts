/**
 * 트레이너 화면 설정 (서버 데이터에 없는 화면용 정보만 둡니다).
 * 인물 목록·이름·타입·파티·체육관 번호(badge_order)는 트레이너 API(GET /api/trainers)에서 받습니다.
 */

export interface GymCity {
  id: string;
  /** 체육관이 있는 시티 이름 (서버 데이터에 없어 화면에서 정함) */
  name: string;
}

/** 체육관 시티. 순서 = 체육관 번호(badge_order) 1~8 */
export const GYM_CITIES: readonly GymCity[] = [
  { id: "city-1", name: "성신시티" },
  { id: "city-2", name: "칠보시티" },
  { id: "city-3", name: "구름시티" },
  { id: "city-4", name: "뇌문시티" },
  { id: "city-5", name: "물풍경시티" },
  { id: "city-6", name: "궐수시티" },
  { id: "city-7", name: "설화시티" },
  { id: "city-8", name: "쌍용시티" },
];

/** 챔피언 ID (연출·잠금 규칙에 씁니다) */
export const CHAMPION_ID = "alder";

/** 플라스마단 게치스 ID. 나머지 플라스마단(N)은 API가 스토리 순서로 줍니다. */
export const PLASMA_GHETSIS_ID = "ghetsis";

/** 게임 버전 */
export type GameVersion = "black" | "white";

/**
 * 버전마다 다른 상대 (같은 자리, 다른 사람).
 * - 8번 체육관: 블랙 = 사간, 화이트 = 아이리스
 * - N의 성: 블랙·화이트 각각
 * 여기 없는 트레이너는 두 버전 모두 나옵니다.
 */
export const VERSION_ONLY: Readonly<Record<string, GameVersion>> = {
  drayden: "black",
  iris: "white",
  "n-castle-black": "black",
  "n-castle-white": "white",
};

/**
 * 지금 고른 게임 버전. null이면 두 버전을 모두 보여 줍니다.
 * 스토리 진행(사용자 진행도)을 연결할 때 사용자가 고른 버전으로 바뀝니다.
 */
export const CURRENT_VERSION: GameVersion | null = null;

/** 버전에 맞는 트레이너만 남깁니다. version이 null이면 그대로 둡니다. */
export function forVersion(ids: readonly string[], version: GameVersion | null = CURRENT_VERSION): string[] {
  return ids.filter((id) => version === null || VERSION_ONLY[id] === undefined || VERSION_ONLY[id] === version);
}

/** 인물 이미지 경로 (public/trainer-images/). 파일이 없으면 이름 첫 글자 타일을 씁니다. */
export const TRAINER_IMAGE_BASE = "/trainer-images";

/** 이미지 파일 이름. N은 한 장을 공유합니다. (트레이너 API의 image는 아직 비어 있어 화면 쪽 사진을 씁니다) */
export function imageIdFor(trainerId: string): string {
  return trainerId.startsWith("n-") ? "n" : trainerId;
}

/** 인물 사진 주소. format으로 WebP(기본, 고해상도)와 PNG를 고릅니다. */
/** 칸과 팝오버에 쓰는 사진 형식. GIF를 받으면 여기만 "gif"로 바꾸면 됩니다. */
export const PORTRAIT_FORMAT: "png" | "gif" = "png";

/**
 * 상대 파티 화면의 큰 인물 칸에서 움직이는 GIF를 쓰는 인물 (이미지 ID 기준, 파일: public/trainer-images/{id}.gif).
 * 연무는 받은 GIF, 나머지는 전신 PNG로 만든 숨쉬기 GIF입니다.
 */
const DETAIL_GIF_IDS: ReadonlySet<string> = new Set([
  "marshal", "shauntal", "grimsley", "caitlin", "alder", "ghetsis", "n",
  "cress", "chili", "cilan", "lenora", "burgh", "elesa", "clay", "skyla", "brycen", "drayden", "iris",
]);

/** 상대 파티 화면의 큰 인물 사진 주소. GIF가 있는 인물은 GIF, 나머지는 칸 사진(PNG)입니다. */
export function detailPortraitSrc(trainerId: string): string {
  return trainerImageSrc(trainerId, DETAIL_GIF_IDS.has(imageIdFor(trainerId)) ? "gif" : PORTRAIT_FORMAT);
}

/** 상반신 사진 (128×64, public/trainer-images/bust/). 등장 연출 띠에 씁니다. 패널·상세는 전신 그림입니다. */
export function trainerBustSrc(trainerId: string): string {
  return `${TRAINER_IMAGE_BASE}/bust/${imageIdFor(trainerId)}.png`;
}

export function trainerImageSrc(trainerId: string, format: "webp" | "png" | "gif" = "webp"): string {
  return `${TRAINER_IMAGE_BASE}/${imageIdFor(trainerId)}.${format}`;
}
