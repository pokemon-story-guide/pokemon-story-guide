/**
 * 메인 메뉴 항목 정의.
 * 메뉴 이름과 경로를 여기서만 바꾸면 메인 화면과 라우팅에 함께 반영됩니다.
 * 각 기능은 나중에 API와 연결하며, 지금은 자리표시자 화면을 보여 줍니다.
 */
export type MenuId = "map" | "trainers" | "pokemon";

export interface MenuItem {
  id: MenuId;
  label: string;
  description: string;
  path: string;
}

export const MENU_ITEMS: readonly MenuItem[] = [
  {
    id: "map",
    label: "맵 정보",
    description: "장소별 출현 포켓몬을 확인합니다.",
    path: "/map",
  },
  {
    id: "trainers",
    label: "트레이너 정보",
    description: "관장과 사천왕의 파티를 확인합니다.",
    path: "/trainers",
  },
  {
    id: "pokemon",
    label: "포켓몬 정보",
    description: "포켓몬의 타입, 능력치, 출현 장소를 확인합니다.",
    path: "/pokemon",
  },
];
