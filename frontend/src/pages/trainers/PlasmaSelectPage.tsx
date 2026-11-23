import { useNavigate } from "react-router-dom";
import { MenuList } from "../../components/MenuList";
import { ScreenFrame } from "../../components/ScreenFrame";
import type { MenuItem } from "../../config/menuItems";

const ITEMS: readonly MenuItem[] = [
  { id: "map", label: "게치스", description: "플라스마단 수장", path: "/trainers/detail/ghetsis" },
  { id: "pokemon", label: "N", description: "스토리 순서대로 6번의 대결", path: "/trainers/plasma/n" },
];

/** 플라스마단: 게치스와 N 중 고르기 */
export function PlasmaSelectPage() {
  const navigate = useNavigate();
  return (
    <ScreenFrame title="플라스마단" breadcrumb="트레이너 정보" backTo="/trainers">
      <MenuList items={ITEMS} onSelect={(item) => navigate(item.path)} />
    </ScreenFrame>
  );
}
