import { useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { DesignFrame, DesignTopbar } from "../../components/DesignFrame";
import { useApi, useApiAll, type PokemonCard, type Recommendation, type TrainerCategory, type TrainerDetail } from "../../api/client";
import { StatusView } from "../../components/StatusView";
import { detailPortraitSrc, GYM_CITIES } from "../../config/trainerGroups";
import { bwSpriteUrl, defenseMatchup, multLabel, typeLabel } from "../../lib/pokemon";

const ROLE_LABEL: Record<TrainerCategory, string> = {
  "gym-leader": "관장",
  "elite-four": "사천왕",
  champion: "챔피언",
  plasma: "플라스마단",
};

/** 목록 화면 경로 (뒤로 가기 대상) */
function parentPath(trainer: TrainerDetail): string {
  if (trainer.category === "gym-leader") return "/trainers/gym";
  if (trainer.category === "elite-four" || trainer.category === "champion") return "/trainers/elite";
  if (trainer.id.startsWith("n-")) return "/trainers/plasma/n";
  return "/trainers/plasma";
}

/**
 * 상대 파티 화면 (목업 leader_party 구성). 관장·사천왕·챔피언·플라스마단 공통입니다.
 * - 왼쪽: 인물 정보 / 가운데: 파티 6칸 (상성 버튼으로 기준 포켓몬을 고릅니다) / 오른쪽: 상성 정보, 추천 레벨·추천 포켓몬
 * - 인물 정보와 파티(포켓몬 이름·타입·레벨)는 트레이너 상세 API(GET /api/trainers/{id})에서 받습니다.
 * - 상성은 받은 타입으로 화면에서 계산합니다. 추천 포켓몬은 API 연결 전이라 자리표시자입니다.
 */
export function TrainerDetailPage() {
  const { trainerId } = useParams();
  const api = useApi<TrainerDetail>(trainerId ? `/trainers/${encodeURIComponent(trainerId)}` : null);

  if (!trainerId) {
    return <Navigate to="/trainers" replace />;
  }
  if (api.status !== "ok") {
    return (
      <DesignFrame>
        <DesignTopbar backTo="/trainers" backLabel="트레이너 정보" />
        <div className="status-page">
          <section className="panel">
            <StatusView status={api.status} what="트레이너" error={api.error} onRetry={api.retry} />
          </section>
        </div>
      </DesignFrame>
    );
  }
  return <TrainerDetailView trainer={api.data} />;
}

/**
 * 추천에서 빼는 전설·환상 포켓몬 (data/mon.json의 usable: 0).
 * 포켓몬 API 응답에 usable이 없어 임시로 화면에 둡니다. API에 생기면 그 값으로 바꿉니다.
 */
const LEGENDARY_IDS: ReadonlySet<number> = new Set([0, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155]);

/** 처음 보여 줄 추천 포켓몬 수 (더보기를 누르면 전부) */
const REC_SHOWN = 6;

/**
 * 이 상대에게 추천하는 포켓몬.
 * 임시 방식: 추천 API(#25)에 포켓몬마다 "포켓몬 vs 이 상대" 점수를 물어보고 점수 높은 순으로 줄 세웁니다
 * (약 140번 요청, 처음 한 번 1~2초). 목록 API(예: /api/recommendations/top)가 생기면 요청 부분만 교체합니다.
 */
function RecommendedPokemon({ trainerId }: { trainerId: string }) {
  const [more, setMore] = useState(false);
  const list = useApi<PokemonCard[]>("/pokemon");
  const candidates = (list.data ?? []).filter((p) => !LEGENDARY_IDS.has(p.id));
  const recs = useApiAll<Recommendation>(
    candidates.map((p) => `/recommendations?pokemon_id=${p.id}&trainer_id=${encodeURIComponent(trainerId)}`),
  );

  if (list.status !== "ok" || recs.status !== "ok" || candidates.length === 0) {
    const status = list.status === "error" || recs.status === "error" ? "error" : "loading";
    return (
      <StatusView
        status={status}
        what="추천 포켓몬"
        error={list.error ?? recs.error}
        onRetry={() => {
          list.retry();
          recs.retry();
        }}
      />
    );
  }

  const ranked = candidates
    .map((p, i) => ({ ...p, rec: recs.data[i] }))
    .sort((a, b) => b.rec.score - a.rec.score || a.id - b.id);
  const shown = more ? ranked : ranked.slice(0, REC_SHOWN);
  return (
    <>
      <div className={more ? "recgrid more" : "recgrid"}>
        {shown.map((p, i) => (
          <Link
            key={p.id}
            to={`/pokemon/${p.id}`}
            className={`recmon ${p.rec.rating}`}
            title={[`${p.name} · ${p.rec.rating_label} ${p.rec.score}점`, ...p.rec.reasons.map((r) => `+ ${r}`), ...p.rec.warnings.map((w) => `! ${w}`)].join("\n")}
          >
            <span className="rank">{i + 1}</span>
            <img src={bwSpriteUrl(p.id)} alt="" />
            <span className="rn">{p.name}</span>
            <span className="rs">
              {p.rec.rating_label} {p.rec.score}
            </span>
          </Link>
        ))}
      </div>
      <RecMoreButton more={more} onToggle={() => setMore((m) => !m)} total={ranked.length} />
    </>
  );
}

/** 더보기 버튼: 추천 레벨 줄 오른쪽(예전 "에이스 Lv + 3" 글씨 자리)에 CSS로 위치시킵니다. */
function RecMoreButton({ more, onToggle, total }: { more: boolean; onToggle: () => void; total: number }) {
  return (
    <button type="button" className="recmore" onClick={onToggle} aria-expanded={more}>
      {more ? "접기" : `더보기 (${total})`}
    </button>
  );
}

function TrainerDetailView({ trainer }: { trainer: TrainerDetail }) {
  const [selected, setSelected] = useState(0);
  const roleLabel = ROLE_LABEL[trainer.category];
  // 관장은 체육관 번호(badge_order)로 시티를 찾습니다.
  const cityIndex = trainer.badge_order !== null ? trainer.badge_order - 1 : -1;
  const cityName = cityIndex >= 0 ? GYM_CITIES[cityIndex].name : roleLabel;
  const subLabel = cityIndex >= 0 ? `${cityIndex + 1}번째 체육관` : roleLabel;
  const levels = trainer.party.map((m) => m.level);
  const topLevel = levels.length > 0 ? Math.max(...levels) : 0;
  const ace = topLevel;

  const member = trainer.party[selected];
  const memberRecord = member;
  const matchup = memberRecord ? defenseMatchup(memberRecord.types) : null;

  return (
    <DesignFrame>
      <DesignTopbar backTo={parentPath(trainer)} backLabel={roleLabel} />
      <div className="wrap3">
        {/* 왼쪽: 인물 정보 */}
        <section className="panel leader">
          <div className="ph">
            {roleLabel} 정보<span className="sub">{subLabel}</span>
          </div>
          <div className="pb">
            <div className="portrait">
              {cityIndex >= 0 && <span className="no">No.{cityIndex + 1}</span>}
              <img src={detailPortraitSrc(trainer.id)} alt={trainer.name} />
            </div>
            <div className="lname">{trainer.name}</div>
            {trainer.type && <span className={`type ${trainer.type}`}>{typeLabel(trainer.type)}</span>}
            <div className="city">{cityName}</div>
            <div className="lmeta">
              <span>포켓몬 {trainer.party.length}마리</span>
              <span>최고 Lv.{topLevel}</span>
            </div>
          </div>
        </section>

        {/* 가운데: 포켓몬 파티 6칸 */}
        <section className="panel party">
          <div className="ph">포켓몬 파티</div>
          <div className="pb">
            {Array.from({ length: 6 }, (_, i) => {
              const m = trainer.party[i];
              if (!m) {
                return (
                  <div key={`empty-${i}`} className="prow empty">
                    <div className="mon empty-slot" />
                    <div className="slot">빈 슬롯</div>
                  </div>
                );
              }
              return (
                <div key={`${m.pokemon_id}-${i}`} className={i === selected ? "prow on" : "prow"}>
                  <div className="mon">
                    <img src={m.image ?? bwSpriteUrl(m.pokemon_id)} alt="" />
                  </div>
                  <div className="info">
                    <span className="namebox">{m.name}</span>
                    <span className="types">
                      {m.types.map((t) => (
                        <span key={t} className={`type ${t}`}>
                          {typeLabel(t)}
                        </span>
                      ))}
                    </span>
                    <span className="lv">Lv.{m.level}</span>
                  </div>
                  <button type="button" className="mbtn" onClick={() => setSelected(i)}>
                    상성
                  </button>
                </div>
              );
            })}
          </div>
        </section>

        {/* 오른쪽: 상성 정보, 추천 */}
        <div className="col">
          <section className="panel mu">
            <div className="ph">
              상성 정보<span className="sub">{memberRecord ? `${memberRecord.name} 기준` : "포켓몬 없음"}</span>
            </div>
            <div className="pb">
              {matchup ? (
                <>
                  <div className="mline">
                    <span className="tag good">유리</span>
                    <div className="types">
                      {matchup.advantage.length === 0 && <span className="nonetxt">해당 없음</span>}
                      {matchup.advantage.map((e) => (
                        <span key={e.type} className={`type ${e.type}`}>
                          {typeLabel(e.type)}
                          <em>×{multLabel(e.mult)}</em>
                        </span>
                      ))}
                      <small>이 타입 기술이 {memberRecord?.name}에게 2배 이상 들어가요</small>
                    </div>
                  </div>
                  <div className="mline">
                    <span className="tag bad">불리</span>
                    <div className="types">
                      {[...matchup.disadvantage, ...matchup.immune].length === 0 && <span className="nonetxt">해당 없음</span>}
                      {[...matchup.disadvantage, ...matchup.immune].map((e) => (
                        <span key={e.type} className={`type ${e.type}`}>
                          {typeLabel(e.type)}
                          <em>×{multLabel(e.mult)}</em>
                        </span>
                      ))}
                      <small>이 타입 기술은 {memberRecord?.name}에게 반감되거나 통하지 않아요</small>
                    </div>
                  </div>
                </>
              ) : (
                <p className="empty">파티 포켓몬을 고르면 상성이 보입니다.</p>
              )}
            </div>
          </section>

          <section className="panel rec" style={{ flex: 1 }}>
            <div className="ph">추천 레벨 · 추천 포켓몬</div>
            <div className="pb">
              <div className="rlv">
                추천 레벨 <b title={`에이스 Lv.${ace} + 3`}>Lv.{ace + 3} 이상</b>
              </div>
              <span className="pill">{trainer.name} 상대 추천 포켓몬</span>
              <RecommendedPokemon trainerId={trainer.id} />
            </div>
          </section>
        </div>
      </div>
    </DesignFrame>
  );
}
