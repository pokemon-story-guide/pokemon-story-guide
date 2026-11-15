import { useNavigate } from "react-router-dom";
import { MenuList } from "../../components/MenuList";
import { ScreenFrame } from "../../components/ScreenFrame";
import type { MenuItem } from "../../config/menuItems";

const ITEMS: readonly MenuItem[] = [
  { id: "map", label: "사천왕", description: "사천왕 4명", path: "/trainers/elite/four" },
  { id: "pokemon", label: "챔피언", description: "챔피언 노간주", path: "/trainers/elite/champion" },
];

/** 사천왕과 챔피언을 구분하는 화면 */
export function EliteSelectPage() {
  const navigate = useNavigate();
  return (
    <ScreenFrame title="사천왕 · 챔피언" breadcrumb="트레이너 정보" backTo="/trainers">
      <MenuList items={ITEMS} onSelect={(item) => navigate(item.path)} />
    </ScreenFrame>
  );
}
