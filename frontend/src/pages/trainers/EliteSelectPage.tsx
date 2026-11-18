import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { EliteIntro } from "../../components/EliteIntro";
import { TRAINERS } from "../../config/trainerData";
import { CHAMPION_ID, ELITE_FOUR_IDS, PORTRAIT_FORMAT, trainerImageSrc } from "../../config/trainerGroups";

/**
 * 챔피언 노간주가 열리는 조건: 사천왕 4명을 모두 이기면 열립니다.
 * 지금은 시연 버튼으로 엽니다. 승리 상태 저장 방식은 나중에 정합니다.
 */

/** 칸의 사진 한 장. 파일이 없으면 이름 첫 글자를 보여 줍니다. */
function Portrait({ id, name, locked }: { id: string; name: string; locked: boolean }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return <span className="gym-card__fallback" aria-hidden="true">{name.charAt(0)}</span>;
  }
  return (
    <img
      className={locked ? "gym-card__portrait gym-card__portrait--shadow" : "gym-card__portrait"}
      src={trainerImageSrc(id, PORTRAIT_FORMAT)}
      alt=""
      onError={() => setFailed(true)}
    />
  );
}

/**
 * 사천왕 · 챔피언 화면.
 * - 왼쪽 2×2는 사천왕 4명, 오른쪽 큰 칸은 챔피언 노간주입니다.
 * - 마우스를 올리면 선택 효과(사진 확대)만 보입니다. 팝오버는 쓰지 않습니다.
 * - 사천왕을 클릭하면 연출이 재생되고, 끝나면 상세 화면으로 갑니다. 챔피언은 열린 뒤에만 반응합니다.
 */
export function EliteSelectPage() {
  const navigate = useNavigate();
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [championUnlocked, setChampionUnlocked] = useState(false);
  /** 사천왕 연출 중인 인물 ID (없으면 null) */
  const [introId, setIntroId] = useState<string | null>(null);
  const championLocked = !championUnlocked;

  const openDetail = (id: string) => navigate(`/trainers/detail/${id}`);
  const enter = (id: string) => setHoverId(id);
  const leave = () => setHoverId(null);

  return (
    <div className="trainer-page">
      <div className="trainer-categories trainer-categories--dark trainer-categories--gym-fill">
        <p className="trainer-categories__title trainer-categories__title--gym">사천왕 · 챔피언</p>

        <div className="trainer-categories__body trainer-categories__body--compact trainer-categories__body--gym">
          <div className="gym-grid elite-grid">
            {ELITE_FOUR_IDS.map((id) => {
              const selected = hoverId === id;
              return (
                <div
                  key={id}
                  className={selected ? "gym-card gym-card--selected" : "gym-card"}
                  aria-label={`${TRAINERS[id].name} 사천왕`}
                  onMouseEnter={() => enter(id)}
                  onMouseLeave={leave}
                  onClick={() => setIntroId(id)}
                >
                  <span className="gym-card__image">
                    <Portrait id={id} name={TRAINERS[id].name} locked={false} />
                  </span>
                </div>
              );
            })}

            <div
              className={
                championLocked
                  ? "gym-card gym-card--locked elite-champion"
                  : hoverId === CHAMPION_ID
                    ? "gym-card gym-card--selected elite-champion"
                    : "gym-card elite-champion"
              }
              aria-label={`${TRAINERS[CHAMPION_ID].name} 챔피언${championLocked ? " (잠김)" : ""}`}
              aria-disabled={championLocked}
              onMouseEnter={() => !championLocked && enter(CHAMPION_ID)}
              onMouseLeave={leave}
              onClick={() => !championLocked && openDetail(CHAMPION_ID)}
            >
              <span className="gym-card__image">
                <Portrait id={CHAMPION_ID} name={TRAINERS[CHAMPION_ID].name} locked={championLocked} />
              </span>
            </div>
          </div>
        </div>

        <div className="trainer-categories__footer">
          {/* 시연용: 챔피언 열기. 실제에서는 사천왕 4명 승리 시 열립니다. */}
          <button
            type="button"
            className="demo-unlock"
            onClick={() => setChampionUnlocked(true)}
            disabled={championUnlocked}
          >
            챔피언 열기 (시연)
          </button>
          <Link to="/" className="return-icon" aria-label="메인으로" title="메인으로">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M3 12a9 9 0 1 0 3-6.7" />
              <path d="M3 4v5h5" />
            </svg>
          </Link>
        </div>
      </div>

      {introId !== null && <EliteIntro id={introId} onDone={() => openDetail(introId)} />}

    </div>
  );
}
