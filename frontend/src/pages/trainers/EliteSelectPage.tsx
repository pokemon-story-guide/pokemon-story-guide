import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { DesignFrame, DesignTopbar } from "../../components/DesignFrame";
import { EliteIntro } from "../../components/EliteIntro";
import { LeaderFlags, type FlagItem, type FlagPerson } from "../../components/LeaderFlags";
import { UnlockTrack } from "../../components/UnlockTrack";
import { TrainersGate, type TrainerGroups } from "../../api/trainers";
import { CHAMPION_ID } from "../../config/trainerGroups";
import { TYPE_COLOR, typeLabel } from "../../lib/pokemon";
import { playSound, SOUND_CHOOSE } from "../../sound";

/** 챔피언 노간주의 깃발 색 (목업의 노란 깃발 색) */
const CHAMPION_COLOR = "#e8b919";

/**
 * 사천왕 및 챔피언 화면 (목업 leader_select 틀). 왼쪽 구역에 사천왕 4명, 오른쪽 구역에 챔피언 혼자 큰 깃발로 둡니다.
 * - 사천왕 4명은 연출 후 상대 파티 화면으로 갑니다.
 * - 챔피언은 사천왕 4명을 모두 이긴 뒤에만 열립니다. 지금은 시연 버튼으로 엽니다.
 */
export function EliteSelectPage() {
  const navigate = useNavigate();
  const [championUnlocked, setChampionUnlocked] = useState(false);
  /** 챔피언까지의 진행도 (0~1). 오른쪽 끝(1)에 몬스터볼이 닿으면 챔피언이 열립니다. */
  const [progress, setProgress] = useState(0);
  const [intro, setIntro] = useState<{ id: string; key: number } | null>(null);
  const introSeq = useRef(0);

  /** 왼쪽 구역: 사천왕 4명 (API 순서) */
  const eliteFlags = (groups: TrainerGroups): FlagItem[] =>
    groups.eliteFour.map((t) => ({
      key: t.id,
      color: TYPE_COLOR[t.type ?? "normal"],
      people: [{ id: t.id, name: t.name }],
      sub: t.type ? typeLabel(t.type) : undefined,
    }));

  /** 오른쪽 구역: 챔피언 혼자 */
  const championFlags = (groups: TrainerGroups): FlagItem[] =>
    groups.champion
      ? [
          {
            key: groups.champion.id,
            color: CHAMPION_COLOR,
            people: [{ id: groups.champion.id, name: groups.champion.name }],
            locked: !championUnlocked,
            sub: championUnlocked ? "하나지방 챔피언" : "잠김",
          },
        ]
      : [];

  const handlePick = (person: FlagPerson) => {
    playSound(SOUND_CHOOSE);
    introSeq.current += 1;
    setIntro({ id: person.id, key: introSeq.current });
  };

  return (
    <DesignFrame>
      <DesignTopbar backTo="/trainers" backLabel="트레이너 정보" />
      <TrainersGate>
        {(groups) => (
          <>
            <LeaderFlags
              group="elite"
              flags={eliteFlags(groups)}
              aside={{
                group: "champion",
                flags: championFlags(groups),
                between: (
                  <UnlockTrack progress={progress} onArrive={() => setChampionUnlocked(true)} label="챔피언까지 진행도" />
                ),
              }}
              onPick={handlePick}
            />
            <div className="flag-footer">
              <span className="flag-note">사천왕 4명 · 챔피언 1명{championUnlocked ? "" : " (사천왕 4명을 이기면 열립니다)"}</span>
              {/* 시연용: 챔피언 열기. 몬스터볼이 끝까지 굴러가면 열립니다. 실제에서는 사천왕 4명 승리 시 진행됩니다. */}
              <button type="button" className="demo-btn" onClick={() => setProgress(1)} disabled={progress >= 1}>
                챔피언 열기 (시연)
              </button>
            </div>
            {intro !== null && (
              <EliteIntro
                key={intro.key}
                id={intro.id}
                name={groups.byId[intro.id]?.name ?? ""}
                layout={intro.id === CHAMPION_ID ? "champion" : "elite"}
                onDone={() => navigate(`/trainers/detail/${intro.id}`)}
              />
            )}
          </>
        )}
      </TrainersGate>
    </DesignFrame>
  );
}
