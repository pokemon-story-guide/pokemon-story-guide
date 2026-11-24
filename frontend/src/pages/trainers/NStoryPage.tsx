import { Fragment, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { TrainerSummary } from "../../api/client";
import { TrainersGate } from "../../api/trainers";
import { DesignFrame, DesignTopbar } from "../../components/DesignFrame";
import { playSound, SOUND_CHOOSE } from "../../sound";
import nUrl from "../../data/plasma/plasma-n.png";

/** 처음에 깬 스토리 수. 0이면 1번째 스토리만 열려 있습니다. */
const START_CLEARED = 0;

/** 스토리 클리어 시연의 효과 시간(ms). 그림자 → N 색 전환 시간과 맞춥니다. */
const CLEAR_MS = 900;

/** "N (칠보시티)" → "칠보시티" */
function placeOf(name: string): string {
  const m = name.match(/\((.+)\)/);
  return m ? m[1] : name;
}

/**
 * N 스토리 목록 (스토리 순서, 관장 선택처럼 차례로 풀림).
 * - N 목록·순서·이름은 트레이너 API(플라스마단 중 게치스를 뺀 순서)를 따릅니다.
 * - 열린 스토리만 N이 보이고, 잠긴 스토리는 그림자로 보입니다.
 * - 스토리를 깨면 노란 화살표가 다음 스토리를 가리키고, 다음 칸의 그림자가 N으로 바뀝니다.
 * - 열린 N을 누르면 그 스토리의 상대 파티 화면으로 갑니다. (N 연출은 플라스마단 화면에서 N을 고를 때 나옵니다)
 * 블랙·화이트 전용 N의 성은 고른 버전(CURRENT_VERSION)의 것만 보입니다. 지금은 버전 선택 전이라 둘 다 보입니다.
 */
export function NStoryPage() {
  return (
    <DesignFrame>
      <DesignTopbar backTo="/trainers/plasma" backLabel="플라스마단" />
      <TrainersGate>{(groups) => <NStoryBoard stories={groups.nStory} />}</TrainersGate>
    </DesignFrame>
  );
}

function NStoryBoard({ stories }: { stories: TrainerSummary[] }) {
  const navigate = useNavigate();
  const [cleared, setCleared] = useState(START_CLEARED);
  const [clearing, setClearing] = useState(false);
  const total = stories.length;
  /** 열린 스토리 수 = 깬 수 + 1 (마지막 스토리까지) */
  const unlocked = Math.min(cleared + 1, total);

  const handlePick = (id: string, index: number) => {
    if (index >= unlocked) return;
    playSound(SOUND_CHOOSE);
    navigate(`/trainers/detail/${id}`);
  };

  /** 시연용: 지금 스토리를 깨고 다음 스토리를 엽니다. 실제에서는 N과의 배틀 승리 시 호출됩니다. */
  const handleClear = () => {
    if (clearing || cleared >= total) return;
    setClearing(true);
    window.setTimeout(() => {
      setCleared((n) => Math.min(n + 1, total));
      setClearing(false);
    }, CLEAR_MS);
  };

  return (
    <>
      <div className="nstory-page">
        <section className="panel nstory-panel">
          <div className="ph">
            N 스토리<span className="sub">스토리를 깨면 다음 만남이 열립니다</span>
          </div>
          <div className="nstory-row">
            {stories.map((t, index) => {
              const locked = index >= unlocked;
              const done = index < cleared;
              const classes = ["nstep"];
              if (locked) classes.push("locked");
              else if (done) classes.push("done");
              else classes.push("now");
              return (
                <Fragment key={t.id}>
                  {index > 0 && (
                    <span className={index <= cleared ? "narrow on" : "narrow"} aria-hidden="true">
                      <i />
                    </span>
                  )}
                  <button
                    type="button"
                    className={classes.join(" ")}
                    onClick={() => handlePick(t.id, index)}
                    aria-disabled={locked}
                    aria-label={locked ? `스토리 ${index + 1} (잠김)` : `스토리 ${index + 1}: ${t.name}`}
                  >
                    <span className="no">STORY {index + 1}</span>
                    <span className="face">
                      <img src={nUrl} alt="" />
                    </span>
                    <span className="place">{placeOf(t.name)}</span>
                  </button>
                </Fragment>
              );
            })}
          </div>
        </section>
      </div>
      <div className="flag-footer">
        <span className="flag-note">
          N 스토리 {total}개 · 깬 스토리 {cleared} / {total}
        </span>
        {/* 시연용: 스토리 클리어. 실제에서는 N과의 배틀 승리 시 호출됩니다. 진행 상태 저장은 나중에 연결합니다. */}
        <button type="button" className="demo-btn" onClick={handleClear} disabled={clearing || cleared >= total}>
          스토리 클리어 (시연)
        </button>
      </div>
    </>
  );
}
