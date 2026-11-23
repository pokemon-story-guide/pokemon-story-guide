import { useNavigate } from "react-router-dom";
import { MenuList } from "../components/MenuList";
import { MENU_ITEMS } from "../config/menuItems";
import titleLogo from "../data/screens/title-logo.png";

/**
 * 메인 화면: 제목 영역 + 메뉴 선택.
 * API 호출은 없고, 메뉴를 고르면 소리를 내고 해당 화면으로 이동합니다.
 */
export function MainMenuPage() {
  const navigate = useNavigate();

  return (
    <div className="main-menu">
        {/* 로고 자리: 디자인이 정해지면 여기에 넣습니다. */}
        <div className="main-menu__logo" aria-label="로고 자리">
          <h1 className="main-menu__title">
            <img src={titleLogo} alt="PokéNav 포켓몬 스토리 공략 도우미" />
          </h1>
        </div>

        <section className="main-menu__panel">
          <MenuList items={MENU_ITEMS} onSelect={(item) => {
                          navigate(item.path);
            }} />
        </section>
    </div>
  );
}
