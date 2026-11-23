import { GYM_CITIES } from "./trainerGroups";

/**
 * 관장 선택 화면의 카드 8개 (관장 8명 = 배지 1~8번).
 * 1번 카드는 같은 시티의 관장 3명을 팝오버(Y자 배치)로 보여 줍니다.
 */
export interface GymCard {
  badge: number;
  cityName: string;
  /** 카드 하나가 여는 관장 ID 목록. 1번 카드만 3명입니다. */
  leaderIds: string[];
  /** 칸에 보이는 대표 관장 ID */
  imageId: string;
}

/** 1번 칸(성신시티)의 대표 사진은 덴트입니다. */
const REPRESENTATIVE_OVERRIDE: Record<number, string> = { 0: "cilan" };

export const GYM_CARDS: readonly GymCard[] = GYM_CITIES.map((city, index) => ({
  badge: index + 1,
  cityName: city.name,
  leaderIds: city.leaderIds,
  imageId: REPRESENTATIVE_OVERRIDE[index] ?? city.leaderIds[0],
}));
