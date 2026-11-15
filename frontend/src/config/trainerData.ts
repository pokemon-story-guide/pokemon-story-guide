/**
 * 트레이너 데이터 (시연용).
 * 출처: bw_trainers_DataV2.zip (블랙·화이트 기준, 팀 데이터).
 * 2단계에서 /api/trainers 연결 후 이 파일을 제거합니다.
 * party의 pokemonId는 전국 도감 번호입니다. 포켓몬 이름은 아직 연결하지 않았습니다.
 */
export interface PartyMember {
  pokemonId: number;
  level: number;
}

export interface TrainerRecord {
  id: string;
  name: string;
  role: "gym-leader" | "elite-four" | "champion" | "plasma";
  /** 타입 (관장·사천왕). 없으면 null */
  type: string | null;
  /** 버전 전용 인물이면 버전 이름 */
  version: "black" | "white" | null;
  party: PartyMember[];
}

export const TRAINERS: Record<string, TrainerRecord> = {
  "alder": { id: "alder", name: "노간주", role: "champion", type: null, version: null, party: [{"pokemonId": 123, "level": 75}, {"pokemonId": 132, "level": 75}, {"pokemonId": 127, "level": 75}, {"pokemonId": 90, "level": 75}, {"pokemonId": 95, "level": 75}, {"pokemonId": 143, "level": 77}] },
  "brycen": { id: "brycen", name: "담죽", role: "gym-leader", type: "ice", version: null, party: [{"pokemonId": 89, "level": 37}, {"pokemonId": 121, "level": 37}, {"pokemonId": 120, "level": 39}] },
  "burgh": { id: "burgh", name: "아티", role: "gym-leader", type: "bug", version: null, party: [{"pokemonId": 50, "level": 21}, {"pokemonId": 63, "level": 21}, {"pokemonId": 48, "level": 23}] },
  "caitlin": { id: "caitlin", name: "카틀레야", role: "elite-four", type: "psychic", version: null, party: [{"pokemonId": 85, "level": 48}, {"pokemonId": 24, "level": 48}, {"pokemonId": 67, "level": 48}, {"pokemonId": 82, "level": 50}] },
  "chili": { id: "chili", name: "팟", role: "gym-leader", type: "fire", version: null, party: [{"pokemonId": 12, "level": 12}, {"pokemonId": 19, "level": 14}] },
  "cilan": { id: "cilan", name: "덴트", role: "gym-leader", type: "grass", version: null, party: [{"pokemonId": 12, "level": 12}, {"pokemonId": 17, "level": 14}] },
  "clay": { id: "clay", name: "야콘", role: "gym-leader", type: "ground", version: null, party: [{"pokemonId": 58, "level": 29}, {"pokemonId": 42, "level": 29}, {"pokemonId": 36, "level": 31}] },
  "cress": { id: "cress", name: "콘", role: "gym-leader", type: "water", version: null, party: [{"pokemonId": 12, "level": 12}, {"pokemonId": 21, "level": 14}] },
  "drayden": { id: "drayden", name: "사간", role: "gym-leader", type: "dragon", version: "black", party: [{"pokemonId": 117, "level": 41}, {"pokemonId": 127, "level": 41}, {"pokemonId": 118, "level": 43}] },
  "elesa": { id: "elesa", name: "카밀레", role: "gym-leader", type: "electric", version: null, party: [{"pokemonId": 93, "level": 25}, {"pokemonId": 93, "level": 25}, {"pokemonId": 29, "level": 27}] },
  "ghetsis": { id: "ghetsis", name: "게치스", role: "plasma", type: null, version: null, party: [{"pokemonId": 69, "level": 52}, {"pokemonId": 132, "level": 52}, {"pokemonId": 43, "level": 52}, {"pokemonId": 131, "level": 52}, {"pokemonId": 110, "level": 52}, {"pokemonId": 141, "level": 54}] },
  "grimsley": { id: "grimsley", name: "블래리", role: "elite-four", type: "dark", version: null, party: [{"pokemonId": 66, "level": 48}, {"pokemonId": 16, "level": 48}, {"pokemonId": 59, "level": 48}, {"pokemonId": 131, "level": 50}] },
  "iris": { id: "iris", name: "아이리스", role: "gym-leader", type: "dragon", version: "white", party: [{"pokemonId": 117, "level": 41}, {"pokemonId": 127, "level": 41}, {"pokemonId": 118, "level": 43}] },
  "lenora": { id: "lenora", name: "알로에", role: "gym-leader", type: "normal", version: null, party: [{"pokemonId": 13, "level": 18}, {"pokemonId": 11, "level": 20}] },
  "marshal": { id: "marshal", name: "연무", role: "elite-four", type: "fighting", version: null, party: [{"pokemonId": 44, "level": 48}, {"pokemonId": 45, "level": 48}, {"pokemonId": 40, "level": 48}, {"pokemonId": 126, "level": 50}] },
  "n-accumula-town": { id: "n-accumula-town", name: "N (칠보시티)", role: "plasma", type: null, version: null, party: [{"pokemonId": 15, "level": 7}] },
  "n-castle-black": { id: "n-castle-black", name: "N (N의 성 · 블랙)", role: "plasma", type: null, version: "black", party: [{"pokemonId": 150, "level": 52}, {"pokemonId": 71, "level": 50}, {"pokemonId": 90, "level": 50}, {"pokemonId": 73, "level": 50}, {"pokemonId": 77, "level": 50}, {"pokemonId": 107, "level": 50}] },
  "n-castle-white": { id: "n-castle-white", name: "N (N의 성 · 화이트)", role: "plasma", type: null, version: "white", party: [{"pokemonId": 149, "level": 52}, {"pokemonId": 71, "level": 50}, {"pokemonId": 90, "level": 50}, {"pokemonId": 73, "level": 50}, {"pokemonId": 77, "level": 50}, {"pokemonId": 107, "level": 50}] },
  "n-chargestone-cave": { id: "n-chargestone-cave", name: "N (전기돌동굴)", role: "plasma", type: null, version: null, party: [{"pokemonId": 31, "level": 28}, {"pokemonId": 103, "level": 28}, {"pokemonId": 101, "level": 28}, {"pokemonId": 105, "level": 28}] },
  "n-nacrene-city": { id: "n-nacrene-city", name: "N (벽화시티)", role: "plasma", type: null, version: null, party: [{"pokemonId": 25, "level": 13}, {"pokemonId": 41, "level": 13}, {"pokemonId": 38, "level": 13}] },
  "n-nimbasa-city": { id: "n-nimbasa-city", name: "N (뇌문시티)", role: "plasma", type: null, version: null, party: [{"pokemonId": 57, "level": 22}, {"pokemonId": 60, "level": 22}, {"pokemonId": 65, "level": 22}, {"pokemonId": 67, "level": 22}] },
  "shauntal": { id: "shauntal", name: "망초", role: "elite-four", type: "ghost", version: null, party: [{"pokemonId": 69, "level": 48}, {"pokemonId": 99, "level": 48}, {"pokemonId": 129, "level": 48}, {"pokemonId": 115, "level": 50}] },
  "skyla": { id: "skyla", name: "풍란", role: "gym-leader", type: "flying", version: null, party: [{"pokemonId": 34, "level": 33}, {"pokemonId": 27, "level": 33}, {"pokemonId": 87, "level": 35}] },
};
