import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { DesignFrame, DesignTopbar } from "../../components/DesignFrame";
import { EliteIntro } from "../../components/EliteIntro";
import { LeaderFlags, type FlagItem, type FlagPerson } from "../../components/LeaderFlags";
import { TrainersGate, type TrainerGroups } from "../../api/trainers";
import { GYM_CITIES } from "../../config/trainerGroups";
import { TYPE_COLOR } from "../../lib/pokemon";
import { playSound, SOUND_CHOOSE } from "../../sound";

/** 처음 열려 있는 관장 수. 1이면 1번 관장(성신시티)만 열려 있습니다. */
const START_UNLOCKED = 1;

/** 뱃지 채우기 시연의 효과 시간(ms). 잠금 해제 색 전환 시간과 맞춥니다. */
const FILL_MS = 900;

/** 1번 시티(갈색)와 8번 시티(남색)는 목업대로 고정 색을 씁니다. 나머지는 관장 타입 색입니다. */
const CITY_COLOR_OVERRIDE: Record<number, string> = { 0: "#8a5a3b", 7: "#2b3a7a" };

/**
 * 관장 선택 화면 (목업 leader_select). 깃발 8개, 한 깃발에 여러 명이 있을 수 있습니다.
 * - 열린 깃발만 인물이 보이고, 잠긴 깃발은 그림자로 보입니다.
 * - 인물을 누르면 연출 후 그 관장의 상대 파티 화면으로 갑니다.
 */
export function GymSelectPage() {
  const navigate = useNavigate();
  const [unlocked, setUnlocked] = useState(START_UNLOCKED);
  const [filling, setFilling] = useState(false);
  const [intro, setIntro] = useState<{ id: string; key: number } | null>(null);
  const introSeq = useRef(0);

  /** 체육관 번호(badge_order)로 관장을 묶습니다. 버전마다 다른 관장(8번)은 고른 버전만 남습니다. */
  const flagsOf = (groups: TrainerGroups): FlagItem[] =>
    GYM_CITIES.map((city, index) => {
      const leaders = groups.gym(index + 1);
      return {
        key: city.id,
        color: CITY_COLOR_OVERRIDE[index] ?? TYPE_COLOR[leaders[0]?.type ?? "normal"],
        people: leaders.map((t) => ({ id: t.id, name: t.name })),
        locked: index >= unlocked,
        sub: city.name,
      };
    });

  const handlePick = (person: FlagPerson) => {
    playSound(SOUND_CHOOSE);
    introSeq.current += 1;
    setIntro({ id: person.id, key: introSeq.current });
  };

  /** 시연용: 다음 관장의 뱃지를 채웁니다. 실제에서는 관장 승리 시 호출됩니다. */
  const handleFill = () => {
    if (filling || unlocked >= GYM_CITIES.length) return;
    setFilling(true);
    window.setTimeout(() => {
      setUnlocked((n) => Math.min(n + 1, GYM_CITIES.length));
      setFilling(false);
    }, FILL_MS);
  };

  return (
    <DesignFrame>
      <DesignTopbar backTo="/trainers" backLabel="트레이너 정보" />
      <TrainersGate>
        {(groups) => (
          <>
            <LeaderFlags group="gym" flags={flagsOf(groups)} onPick={(person) => handlePick(person)} />
            <div className="flag-footer">
              <span className="flag-note">관장 8명 · 열린 체육관 {Math.min(unlocked, GYM_CITIES.length)} / {GYM_CITIES.length}</span>
              {/* 시연용: 뱃지 채우기. 실제에서는 관장 승리 시 호출됩니다. 진행 상태 저장은 나중에 연결합니다. */}
              <button type="button" className="demo-btn" onClick={handleFill} disabled={filling || unlocked >= GYM_CITIES.length}>
                뱃지 채우기 (시연)
              </button>
            </div>
            {intro !== null && (
              <EliteIntro
                key={intro.key}
                id={intro.id}
                name={groups.byId[intro.id]?.name ?? ""}
                onDone={() => navigate(`/trainers/detail/${intro.id}`)}
              />
            )}
          </>
        )}
      </TrainersGate>
    </DesignFrame>
  );
}
