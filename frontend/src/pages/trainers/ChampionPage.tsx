import { Link } from "react-router-dom";
import { ScreenFrame } from "../../components/ScreenFrame";
import { CHAMPION_ID } from "../../config/trainerGroups";

/**
 * 챔피언 노간주 진입 화면.
 * 등장 효과는 아직 미정이라 자리만 두었습니다. 효과가 정해지면 이 화면에서 구현합니다.
 */
export function ChampionPage() {
  return (
    <ScreenFrame title="챔피언" breadcrumb="트레이너 정보 > 사천왕 · 챔피언" backTo="/trainers/elite">
      <div className="champion-entry">
        {/* 등장 효과 자리 (미정) */}
        <p className="placeholder">등장 효과 자리 (미정)</p>
        <Link to={`/trainers/detail/${CHAMPION_ID}`} className="back-link">
          노간주 정보 보기
        </Link>
      </div>
    </ScreenFrame>
  );
}
