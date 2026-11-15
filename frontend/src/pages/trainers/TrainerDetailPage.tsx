import { useState } from "react";
import { Navigate, useParams } from "react-router-dom";
import { ScreenFrame } from "../../components/ScreenFrame";
import { TRAINERS, type TrainerRecord } from "../../config/trainerData";
import { trainerImageSrc } from "../../config/trainerGroups";

const ROLE_LABEL: Record<TrainerRecord["role"], string> = {
  "gym-leader": "관장",
  "elite-four": "사천왕",
  champion: "챔피언",
  plasma: "플라스마단",
};

/** 목록 화면 경로 (뒤로 가기 대상) */
function parentPath(trainer: TrainerRecord): string {
  if (trainer.role === "gym-leader") return "/trainers/gym";
  if (trainer.role === "elite-four") return "/trainers/elite/four";
  if (trainer.role === "champion") return "/trainers/elite/champion";
  if (trainer.id.startsWith("n-")) return "/trainers/plasma/n";
  return "/trainers/plasma";
}

/**
 * 관장·사천왕·챔피언·플라스마단 공통 상세 화면 (UI-08 구성).
 * 1 인물 정보 / 2 보유 파티 / 3 타입별 상성 / 4 추천 레벨·포켓몬.
 * 3, 4는 데이터 연결 전이라 자리표시자입니다.
 */
export function TrainerDetailPage() {
  const { trainerId } = useParams();
  const trainer = trainerId ? TRAINERS[trainerId] : undefined;
  const [imageFailed, setImageFailed] = useState(false);

  if (!trainer) {
    return <Navigate to="/trainers" replace />;
  }

  return (
    <ScreenFrame title={trainer.name} breadcrumb={`트레이너 정보 > ${ROLE_LABEL[trainer.role]}`} backTo={parentPath(trainer)}>
      <div className="detail-grid">
        <section className="detail-section">
          <h2 className="detail-section__title">1. 인물 정보</h2>
          <div className="detail-profile">
            <span className="detail-profile__image">
              {imageFailed ? (
                <span className="trainer-card__fallback" aria-hidden="true">
                  {trainer.name.charAt(0)}
                </span>
              ) : (
                <img src={trainerImageSrc(trainer.id)} alt={trainer.name} onError={() => setImageFailed(true)} />
              )}
            </span>
            <p className="detail-profile__name">{trainer.name}</p>
            <p className="detail-profile__sub">
              {ROLE_LABEL[trainer.role]}
              {trainer.type ? ` · ${trainer.type}` : ""}
              {trainer.version ? ` · ${trainer.version === "black" ? "블랙" : "화이트"} 전용` : ""}
            </p>
          </div>
        </section>

        <section className="detail-section">
          <h2 className="detail-section__title">2. 보유 파티</h2>
          {trainer.party.length === 0 ? (
            <p className="placeholder">파티 데이터 대기</p>
          ) : (
            <ul className="party-list">
              {trainer.party.map((member, index) => (
                <li key={index} className="party-list__item">
                  <span className="party-list__no">No.{member.pokemonId}</span>
                  <span className="party-list__name">이름 연결 대기</span>
                  <span className="party-list__level">Lv.{member.level}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="detail-section">
          <h2 className="detail-section__title">3. 타입별 상성</h2>
          <p className="placeholder">상성 데이터 연결 대기</p>
        </section>

        <section className="detail-section">
          <h2 className="detail-section__title">4. 추천 레벨 · 포켓몬</h2>
          <p className="placeholder">추천 데이터 연결 대기</p>
        </section>
      </div>
    </ScreenFrame>
  );
}
