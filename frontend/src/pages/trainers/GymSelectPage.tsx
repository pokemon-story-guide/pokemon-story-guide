import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { EliteIntro } from "../../components/EliteIntro";
import { GYM_CARDS } from "../../config/gymSelect";
import { TRAINERS } from "../../config/trainerData";
import { PORTRAIT_FORMAT, trainerImageSrc } from "../../config/trainerGroups";
import { playSound, SOUND_CHOOSE } from "../../sound";

/** 처음 열려 있는 관장 수. 1이면 1번 관장(성신시티)만 열려 있습니다. */
const START_UNLOCKED = 1;

/** 채우기 효과 시간(ms). CSS 애니메이션 길이와 맞춥니다. */
const FILL_MS = 900;

/** 관장이 1명인 카드의 팝오버가 뜨기까지 기다리는 시간(ms). */
const PREVIEW_DELAY_MS = 500;

/** 칸 상태: 잠김(그림자), 채우는 중, 열림 */
type SlotState = "shadow" | "filling" | "earned";

/**
 * 관장 사진 (PNG). 칸과 팝오버 모두 같은 형식을 씁니다.
 * 잠김 상태는 같은 사진을 검은 그림자로 보여 줍니다. 파일이 없으면 이름 첫 글자를 보여 줍니다.
 */
function SlotPicture({ id, name, state }: { id: string; name: string; state: SlotState }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return <span className="gym-card__fallback" aria-hidden="true">{name.charAt(0)}</span>;
  }
  const className =
    state === "shadow"
      ? "gym-card__portrait gym-card__portrait--shadow"
      : state === "filling"
        ? "gym-card__portrait gym-card__portrait--fill"
        : "gym-card__portrait";
  return (
    <img
      className={className}
      src={trainerImageSrc(id, PORTRAIT_FORMAT)}
      alt=""
      onError={() => setFailed(true)}
    />
  );
}

/**
 * 관장 선택 화면 (카드 8개, 4×2). 마우스로만 조작합니다.
 * - 카드에 마우스를 올리면 PNG가 커지는 선택 효과가 보입니다.
 * - 관장이 여러 명인 카드(1번, 8번): 클릭하면 팝오버가 뜹니다. 팝오버 안의 관장을 클릭하면 연출 후 상세로 갑니다.
 *   팝오버는 바깥을 클릭하면 닫힙니다.
 * - 관장이 1명인 카드(2~7번): 마우스를 올리고 0.5초 뒤 팝오버가 뜹니다. 클릭하면 바로 연출 후 상세로 갑니다.
 *   마우스를 떼면 팝오버도 함께 사라집니다.
 * - 연출 중에도 다른 칸을 클릭할 수 있습니다. 진행 중인 연출은 취소되고 새 관장의 연출이 처음부터 시작됩니다.
 */
export function GymSelectPage() {
  const navigate = useNavigate();
  const [unlocked, setUnlocked] = useState(START_UNLOCKED);
  /** 지금 채워지는 중인 칸 번호(없으면 null) */
  /** 처음에는 1번 칸이 채워지는 효과를 한 번 보여 줍니다. */
  const [filling, setFilling] = useState<number | null>(0);
  /** 마우스가 올라가 있는 칸 번호 */
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  /** 팝오버가 열린 칸 번호 */
  const [popIdx, setPopIdx] = useState<number | null>(null);
  const timerRef = useRef<number | null>(null);
  /** 지금 재생 중인 연출(관장 id와 재시작용 key). 없으면 null */
  const [intro, setIntro] = useState<{ id: string; key: number } | null>(null);
  const introSeq = useRef(0);

  /** 화면이 열리면 1번 칸의 채우기 효과가 한 번 끝난 뒤 평소 상태가 됩니다. */
  useEffect(() => {
    const t = window.setTimeout(() => setFilling(null), FILL_MS);
    return () => window.clearTimeout(t);
  }, []);

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    };
  }, []);

  const clearTimer = () => {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  const openDetail = (id: string) => navigate(`/trainers/detail/${id}`);
  const isMulti = (index: number) => GYM_CARDS[index].leaderIds.length > 1;

  /** 연출을 시작합니다. 이미 재생 중이면 취소하고 새 관장으로 다시 시작합니다(key가 바뀌어 다시 그려짐). */
  const startIntro = (id: string) => {
    clearTimer();
    setPopIdx(null);
    introSeq.current += 1;
    setIntro({ id, key: introSeq.current });
  };

  const handleEnter = (index: number) => {
    if (index >= unlocked) return;
    setHoverIdx(index);
    if (!isMulti(index) && intro === null) {
      clearTimer();
      timerRef.current = window.setTimeout(() => {
        setPopIdx(index);
        timerRef.current = null;
      }, PREVIEW_DELAY_MS);
    }
  };

  const handleLeave = (index: number) => {
    setHoverIdx(null);
    clearTimer();
    // 1명짜리 팝오버는 마우스를 떼면 함께 사라집니다. 여러 명짜리는 클릭으로 연 것이라 남겨 둡니다.
    if (popIdx === index && !isMulti(index)) {
      setPopIdx(null);
    }
  };

  const handleClick = (index: number) => {
    if (index >= unlocked) return;
    playSound(SOUND_CHOOSE);
    clearTimer();
    if (isMulti(index)) {
      setPopIdx(index);
    } else {
      startIntro(GYM_CARDS[index].leaderIds[0]);
    }
  };

  const handleFill = () => {
    if (filling !== null || unlocked >= GYM_CARDS.length) return;
    const target = unlocked;
    setFilling(target);
    window.setTimeout(() => {
      setUnlocked((n) => Math.min(n + 1, GYM_CARDS.length));
      setFilling(null);
    }, FILL_MS);
  };

  const popup = popIdx !== null ? GYM_CARDS[popIdx] : null;
  const popupMulti = popIdx !== null && isMulti(popIdx);

  return (
    <div className="trainer-page">
      <div className="trainer-categories trainer-categories--dark trainer-categories--gym-fill">
        <p className="trainer-categories__title trainer-categories__title--gym">관장 선택</p>

        <div className="trainer-categories__body trainer-categories__body--compact trainer-categories__body--gym">
          <div className="gym-stage">
            <div className="gym-grid">
              {GYM_CARDS.map((card, index) => {
                const isOpen = index < unlocked;
                const isFilling = index === filling;
                const slotState: SlotState = isOpen ? "earned" : isFilling ? "filling" : "shadow";
                const lead = card.imageId;
                const classes = ["gym-card"];
                if (isOpen && hoverIdx === index) classes.push("gym-card--selected");
                if (!isOpen) classes.push("gym-card--locked");
                return (
                  <div
                    key={card.badge}
                    className={classes.join(" ")}
                    aria-label={`${card.badge}번 ${card.cityName}${isOpen ? "" : " (잠김)"}`}
                    aria-disabled={!isOpen}
                    onMouseEnter={() => handleEnter(index)}
                    onMouseLeave={() => handleLeave(index)}
                    onClick={() => handleClick(index)}
                  >
                    <span className="gym-card__image">
                      <SlotPicture id={lead} name={TRAINERS[lead].name} state={slotState} />
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="trainer-categories__footer">
          {/* 시연용: 뱃지 채우기. 실제에서는 관장 승리 시 호출됩니다. 진행 상태 저장은 나중에 연결합니다. */}
          <button
            type="button"
            className="demo-unlock"
            onClick={handleFill}
            disabled={filling !== null || unlocked >= GYM_CARDS.length}
          >
            뱃지 채우기 (시연)
          </button>
          <Link to="/" className="return-icon" aria-label="메인으로" title="메인으로">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M3 12a9 9 0 1 0 3-6.7" />
              <path d="M3 4v5h5" />
            </svg>
          </Link>
        </div>
      </div>

      {intro !== null && (
        <EliteIntro key={intro.key} id={intro.id} onDone={() => openDetail(intro.id)} />
      )}

      {popup && (
        <>
          {/* 화면 전체를 어둡게 합니다. 여러 명짜리 팝오버는 바깥을 클릭하면 닫힙니다. */}
          <div
            className={popupMulti ? "gym-dim gym-dim--click" : "gym-dim"}
            onClick={popupMulti ? () => setPopIdx(null) : undefined}
          />
          <div
            className={popupMulti ? "gym-popup" : "gym-popup gym-popup--preview"}
            role="listbox"
            aria-label={`${popup.cityName} 관장`}
          >
            {popup.leaderIds.map((id) => (
              <div key={id} role="option" aria-selected={false} className="gym-mini" onClick={() => { playSound(SOUND_CHOOSE); startIntro(id); }}>
                <span className="gym-mini__image">
                  <SlotPicture id={id} name={TRAINERS[id].name} state="earned" />
                </span>
                <span className="gym-mini__name">{TRAINERS[id].name}</span>
                {TRAINERS[id].version && (
                  <span className="gym-mini__sub">
                    {TRAINERS[id].version === "black" ? "블랙 전용" : "화이트 전용"}
                  </span>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
