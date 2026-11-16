import { ScreenFrame } from "../../components/ScreenFrame";
import { TrainerCard } from "../../components/TrainerCard";
import { ELITE_FOUR_IDS } from "../../config/trainerGroups";
import { TRAINERS } from "../../config/trainerData";

/** 사천왕 4명 카드 (2x2). 카드를 누르면 공통 상세 화면으로 갑니다. */
export function EliteFourPage() {
  return (
    <ScreenFrame title="사천왕" breadcrumb="트레이너 정보 > 사천왕 · 챔피언" backTo="/trainers/elite">
      <div className="card-grid card-grid--two">
        {ELITE_FOUR_IDS.map((id, index) => (
          <TrainerCard
            key={id}
            imageId={id}
            name={TRAINERS[id].name}
            subtitle={`사천왕 ${index + 1}번째${TRAINERS[id].type ? ` · ${TRAINERS[id].type}` : ""}`}
            to={`/trainers/detail/${id}`}
          />
        ))}
      </div>
    </ScreenFrame>
  );
}
