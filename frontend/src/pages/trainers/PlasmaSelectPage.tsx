import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { DesignFrame, DesignTopbar } from "../../components/DesignFrame";
import { LeaderFlags, type FlagItem, type FlagPerson } from "../../components/LeaderFlags";
import { TrainersGate, type TrainerGroups } from "../../api/trainers";
import { PLASMA_GHETSIS_ID } from "../../config/trainerGroups";
import { playSound, SOUND_CHOOSE } from "../../sound";
import { PlasmaIntro, type PlasmaPerson } from "./PlasmaIntro";

/** 플라스마단 깃발 두 개: 게치스(연출 후 상대 파티), N(연출 후 스토리 목록). */
function flagsOf(groups: TrainerGroups): FlagItem[] {
  return [
    {
      key: PLASMA_GHETSIS_ID,
      color: "#8a5a3b",
      people: [{ id: PLASMA_GHETSIS_ID, name: groups.ghetsis?.name ?? "게치스" }],
      sub: "플라스마단",
    },
    { key: "n", color: "#2b3a7a", people: [{ id: "n", name: "N" }], sub: `스토리 ${groups.nStory.length}개` },
  ];
}

/**
 * 플라스마단 화면 (목업 leader_select 틀). 깃발 2개, 깃발 하나에 한 명입니다.
 * - 게치스: 연출을 재생한 뒤 상대 파티 화면으로 갑니다.
 * - N: 같은 번개 연출(N 사진·이름)을 재생한 뒤 스토리 목록 화면으로 갑니다.
 */
export function PlasmaSelectPage() {
  const navigate = useNavigate();
  const [intro, setIntro] = useState<PlasmaPerson | null>(null);

  const handlePick = (person: FlagPerson) => {
    playSound(SOUND_CHOOSE);
    setIntro(person.id === PLASMA_GHETSIS_ID ? "ghetsis" : "n");
  };

  return (
    <DesignFrame>
      <DesignTopbar backTo="/trainers" backLabel="트레이너 정보" />
      <TrainersGate>{(groups) => <LeaderFlags group="plasma" flags={flagsOf(groups)} onPick={handlePick} />}</TrainersGate>
      {intro !== null && (
        <PlasmaIntro
          key={intro}
          who={intro}
          onDone={() => navigate(intro === "ghetsis" ? `/trainers/detail/${PLASMA_GHETSIS_ID}` : "/trainers/plasma/n")}
        />
      )}
    </DesignFrame>
  );
}
