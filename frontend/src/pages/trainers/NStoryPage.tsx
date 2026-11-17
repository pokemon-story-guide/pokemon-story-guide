import { ScreenFrame } from "../../components/ScreenFrame";
import { TrainerCard } from "../../components/TrainerCard";
import { N_STORY_IDS, imageIdFor } from "../../config/trainerGroups";
import { TRAINERS } from "../../config/trainerData";

/**
 * N 목록 (스토리 순서). 스토리 진행에 따른 잠금은 아직 없습니다.
 * 블랙·화이트 전용 N의 성은 목록에 둘 다 있지만, 추후 버전에 맞춰 하나만 보이게 합니다.
 */
export function NStoryPage() {
  return (
    <ScreenFrame title="N" breadcrumb="트레이너 정보 > 플라스마단" backTo="/trainers/plasma">
      <div className="card-grid card-grid--two">
        {N_STORY_IDS.map((id, index) => (
          <TrainerCard
            key={id}
            imageId={imageIdFor(id)}
            name={TRAINERS[id].name}
            subtitle={`스토리 ${index + 1}`}
            to={`/trainers/detail/${id}`}
          />
        ))}
      </div>
    </ScreenFrame>
  );
}
