import chartRaw from "../data/pokemon/type_chart.json";

/**
 * 포켓몬 화면 도우미 (타입 이름·색·상성, 이미지 주소, 검색).
 * - 포켓몬·장소·트레이너 데이터는 서버 API에서 받습니다 (src/api/client.ts).
 * - 하나도감 번호(id 0~155)는 전국도감 번호에서 494를 뺀 값입니다. (0 = 비크티니 = 494번)
 * - type_chart는 "공격 타입 → 방어 타입 배율" 표입니다. 없는 쌍은 1배입니다.
 *   (서버에 타입 상성 API가 없어 백엔드와 같은 5세대 상성표 파일을 씁니다)
 */

export const NATIONAL_OFFSET = 494;

const CHART = chartRaw as unknown as Record<string, Record<string, number>>;

export const TYPE_KEYS: readonly string[] = Object.keys(CHART);

export const TYPE_KO: Record<string, string> = {
  normal: "노말", fire: "불꽃", water: "물", electric: "전기", grass: "풀", ice: "얼음",
  fighting: "격투", poison: "독", ground: "땅", flying: "비행", psychic: "에스퍼", bug: "벌레",
  rock: "바위", ghost: "고스트", dragon: "드래곤", dark: "악", steel: "강철",
};

/** 타입 색 (목업 base.css의 --t-* 값과 같음). 깃발 색으로도 씁니다. */
export const TYPE_COLOR: Record<string, string> = {
  normal: "#9a9a7a", fire: "#ef7a2e", water: "#4f86e8", electric: "#e8b919", grass: "#5fb04a",
  ice: "#5fc2c8", fighting: "#c0392b", poison: "#9b46a3", ground: "#c9a14a", flying: "#8f7be6",
  psychic: "#ef5687", bug: "#93a51c", rock: "#a8923a", ghost: "#6b5a9e", dragon: "#6a3ef0",
  dark: "#5a4a3f", steel: "#9a9ab8",
};

export function typeLabel(type: string): string {
  return TYPE_KO[type] ?? type;
}

export function dexNumber(id: number): string {
  return `No.${String(id).padStart(3, "0")}`;
}

/** 포켓몬 공식 일러스트 (PokéAPI 스프라이트 저장소의 주소를 씁니다. 저장소에는 파일을 넣지 않습니다). */
export function artworkUrl(id: number): string {
  return `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${id + NATIONAL_OFFSET}.png`;
}

/** 블랙·화이트 애니메이션 GIF (PokéAPI 스프라이트 저장소) */
export function bwAnimatedUrl(id: number): string {
  return `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/animated/${id + NATIONAL_OFFSET}.gif`;
}

/** 블랙·화이트 도트 스프라이트 */
export function bwSpriteUrl(id: number): string {
  return `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-v/black-white/${id + NATIONAL_OFFSET}.png`;
}

/**
 * 공격 타입 하나가 방어 타입들(포켓몬의 타입)에게 주는 배율.
 * 예: 땅 공격 → [불꽃, 비행] = 0 (효과 없음), 물 공격 → [불꽃, 땅] = 4
 */
export function attackMultiplier(attack: string, defenders: readonly string[]): number {
  return defenders.reduce((m, d) => m * (CHART[attack]?.[d] ?? 1), 1);
}

/** 포켓몬의 타입들이 방어 타입 하나에게 주는 최대 배율 (포켓몬의 공격 기준) */
export function offenseMultiplier(attackerTypes: readonly string[], defender: string): number {
  return Math.max(...attackerTypes.map((t) => CHART[t]?.[defender] ?? 1));
}

export interface MatchEntry {
  type: string;
  mult: number;
}

/** 방어 기준 상성 (파티 화면): 내 공격 타입이 이 포켓몬에게 어떤 배율인지 */
export function defenseMatchup(defenders: readonly string[]): { advantage: MatchEntry[]; disadvantage: MatchEntry[]; immune: MatchEntry[] } {
  const advantage: MatchEntry[] = [];
  const disadvantage: MatchEntry[] = [];
  const immune: MatchEntry[] = [];
  for (const attack of TYPE_KEYS) {
    const mult = attackMultiplier(attack, defenders);
    if (mult === 0) immune.push({ type: attack, mult });
    else if (mult > 1) advantage.push({ type: attack, mult });
    else if (mult < 1) disadvantage.push({ type: attack, mult });
  }
  advantage.sort((a, b) => b.mult - a.mult);
  disadvantage.sort((a, b) => a.mult - b.mult);
  return { advantage, disadvantage, immune };
}

/** 배율 표기: 4 → ×4, 0.25 → ×¼, 0.5 → ×½ */
export function multLabel(mult: number): string {
  if (mult === 0.25) return "¼";
  if (mult === 0.5) return "½";
  return String(mult);
}

const CHO = ["ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"];

/** 한글 문자열을 초성으로 바꿉니다. 예: 깜눈크 → ㄲㄴㅋ */
export function chosung(text: string): string {
  let out = "";
  for (const ch of text) {
    const code = ch.charCodeAt(0);
    if (code >= 0xac00 && code <= 0xd7a3) out += CHO[Math.floor((code - 0xac00) / 588)];
    else out += ch;
  }
  return out;
}

/** 이름 검색 또는 초성 검색 (질의가 모두 자음이면 초성으로 비교) */
export function matchesQuery(name: string, query: string): boolean {
  const q = query.replace(/\s+/g, "").toLowerCase();
  if (q === "") return true;
  const n = name.replace(/\s+/g, "").toLowerCase();
  if (n.includes(q)) return true;
  if (/^[ㄱ-ㅎ]+$/.test(q)) return chosung(name).includes(q);
  return false;
}
