/**
 * 트레이너 화면의 묶음 구조 (카테고리 → 하위 목록).
 * 시나리오 기준: 관장 8개 시티 / 사천왕·챔피언 / 플라스마단(게치스, N).
 * 시티 이름은 팀 확인 기준으로 적었습니다.
 */

export interface GymCity {
  id: string;
  name: string;
  /** TRAINERS의 키 목록 */
  leaderIds: string[];
}

export const GYM_CITIES: readonly GymCity[] = [
  { id: "city-1", name: "성신시티", leaderIds: ["cress", "chili", "cilan"] },
  { id: "city-2", name: "칠보시티", leaderIds: ["lenora"] },
  { id: "city-3", name: "구름시티", leaderIds: ["burgh"] },
  { id: "city-4", name: "뇌문시티", leaderIds: ["elesa"] },
  { id: "city-5", name: "물풍경시티", leaderIds: ["clay"] },
  { id: "city-6", name: "궐수시티", leaderIds: ["skyla"] },
  { id: "city-7", name: "설화시티", leaderIds: ["brycen"] },
  // 8번 체육관은 버전마다 관장이 다릅니다 (블랙: 사간, 화이트: 아이리스)
  { id: "city-8", name: "쌍용시티", leaderIds: ["drayden", "iris"] },
];

export const ELITE_FOUR_IDS: readonly string[] = ["shauntal", "grimsley", "caitlin", "marshal"];

export const CHAMPION_ID = "alder";

/** 플라스마단: 게치스 1명 + N (스토리 진행 순서) */
export const PLASMA_GHETSIS_ID = "ghetsis";

/**
 * N의 스토리 순서. 블랙·화이트 전용 N의 성은 버전에 따라 하나만 노출합니다.
 * 스토리 진행에 따른 잠금 규칙은 추후 정합니다 (지금은 순서대로 나열만 합니다).
 */
export const N_STORY_IDS: readonly string[] = [
  "n-accumula-town",
  "n-nacrene-city",
  "n-nimbasa-city",
  "n-chargestone-cave",
  "n-castle-black",
  "n-castle-white",
];

/** 인물 이미지 경로 (public/trainer-images/). 파일이 없으면 이름 첫 글자 타일을 씁니다. */
export const TRAINER_IMAGE_BASE = "/trainer-images";

/** 이미지 파일 이름. N은 한 장을 공유합니다. */
export function imageIdFor(trainerId: string): string {
  return trainerId.startsWith("n-") ? "n" : trainerId;
}

/** 인물 사진 주소. format으로 WebP(기본, 고해상도)와 PNG를 고릅니다. */
/** 칸과 팝오버에 쓰는 사진 형식. GIF를 받으면 여기만 "gif"로 바꾸면 됩니다. */
export const PORTRAIT_FORMAT: "png" | "gif" = "png";

export function trainerImageSrc(trainerId: string, format: "webp" | "png" | "gif" = "webp"): string {
  return `${TRAINER_IMAGE_BASE}/${imageIdFor(trainerId)}.${format}`;
}
