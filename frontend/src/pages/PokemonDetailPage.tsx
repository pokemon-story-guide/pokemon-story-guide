import { useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { DesignFrame, DesignTopbar } from "../components/DesignFrame";
import { combineStatus, useApi, useApiAll, type Location, type PokemonDetail, type Recommendation, type TrainerSummary } from "../api/client";
import { useTrainers } from "../api/trainers";
import { StatusView } from "../components/StatusView";
import { markerStyle, placePosition } from "../config/mapGraph";
import { PORTRAIT_FORMAT, trainerImageSrc } from "../config/trainerGroups";
import { artworkUrl, attackMultiplier, bwAnimatedUrl, dexNumber, offenseMultiplier, TYPE_KEYS, typeLabel } from "../lib/pokemon";
import mapUrl from "../data/ui/map-large.png";

/**
 * 목업의 "맵보기" 팝오버: 출현 장소마다 지도 위에 빨간 원이 깜빡입니다.
 * 마을·도로뿐 아니라 꿈터·동굴 같은 특정 장소도 지도의 점 위치에 표시합니다. 위치가 없는 장소는 목록으로만 보입니다.
 */
function MapPopover({ name, places, onClose }: { name: string; places: Location[]; onClose: () => void }) {
  const positions = places.flatMap((place) => {
    const pos = placePosition(place.id);
    return pos ? [{ ...place, ...pos }] : [];
  });
  // 같은 점에 여러 장소(예: 리조트데저트와 고대의 성)가 겹치면 원은 하나만 그립니다.
  const markers = positions.filter((p, i) => positions.findIndex((q) => q.px === p.px && q.py === p.py) === i);
  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="ph">
          출현 위치 · {name}
          <span className="close" role="button" aria-label="닫기" onClick={onClose} />
        </div>
        <div className="mapbox" style={{ width: 774, height: 510, margin: "16px auto 8px", borderRadius: 8 }}>
          <img src={mapUrl} alt="하나지방 지도" />
          <div className="dim" />
          {markers.map((m) => (
            <span
              key={m.id}
              className="mapnode mapnode-red"
              role="img"
              aria-label={m.name}
              title={m.name}
              style={markerStyle(m.px, m.py)}
            />
          ))}
          {markers.length === 0 && <div className="nomap">출현 장소의 지도 위치는 데이터 연결 대기 중입니다</div>}
        </div>
        <div className="mlist">
          {places.map((place) => (
            <span key={place.id} className="chip on">
              {place.name}
            </span>
          ))}
        </div>
        <div className="mfoot">
          <span className="pin" />
          출현 장소 목록입니다
          <span style={{ marginLeft: "auto" }}>바깥 영역을 누르면 닫혀요</span>
        </div>
      </div>
    </div>
  );
}

/**
 * 포켓몬 상세 화면 (목업 detail2 구성).
 * 서버 API에서 받습니다: 기본 정보·진화(GET /api/pokemon/{id}), 출현 장소(GET /api/pokemon/{id}/locations), 관장 타입(GET /api/trainers).
 * 타입 상성과 관장 상성은 받은 타입으로 화면에서 계산합니다.
 * 분류·특성·키·몸무게, 추천 기술, 설명은 API가 없어서 연결 대기 문구를 보여 줍니다.
 */
export function PokemonDetailPage() {
  const { pokemonId } = useParams();
  const id = Number(pokemonId);
  const valid = pokemonId !== undefined && /^\d+$/.test(pokemonId);
  const detail = useApi<PokemonDetail>(valid ? `/pokemon/${id}` : null);
  const places = useApi<Location[]>(valid ? `/pokemon/${id}/locations` : null);
  const trainers = useTrainers();

  if (!valid) {
    return <Navigate to="/pokemon" replace />;
  }

  const all = combineStatus(detail, places, trainers);
  if (all.status !== "ok" || !detail.data || !places.data || !trainers.data) {
    const retry = () => {
      detail.retry();
      places.retry();
      trainers.retry();
    };
    return (
      <DesignFrame>
        <DesignTopbar backTo="/pokemon" backLabel="포켓몬 정보" />
        <div className="status-page">
          <section className="panel">
            <StatusView status={all.status === "ok" ? "loading" : all.status} what="포켓몬" error={all.error} onRetry={retry} />
          </section>
        </div>
      </DesignFrame>
    );
  }

  return <PokemonDetailView pokemon={detail.data} locations={places.data} trainers={trainers.data} />;
}

function PokemonDetailView({
  pokemon,
  locations,
  trainers,
}: {
  pokemon: PokemonDetail;
  locations: Location[];
  trainers: TrainerSummary[];
}) {
  const [mapOpen, setMapOpen] = useState(false);
  const typeNames = pokemon.types.map(typeLabel).join(" · ");

  /** 공격 기준: 이 포켓몬의 타입으로 상대에게 주는 배율 */
  const hits = TYPE_KEYS.filter((d) => offenseMultiplier(pokemon.types, d) >= 2);
  const resisted = TYPE_KEYS.filter((d) => {
    const m = offenseMultiplier(pokemon.types, d);
    return m > 0 && m < 1;
  });
  /** 방어 기준: 상대 공격이 이 포켓몬에게 주는 배율 */
  // 복합 타입은 4배 약점이 생길 수 있어, 4배를 앞에 두고 칩에 ×4를 붙입니다.
  const weakTo = TYPE_KEYS.filter((a) => attackMultiplier(a, pokemon.types) > 1).sort(
    (a, b) => attackMultiplier(b, pokemon.types) - attackMultiplier(a, pokemon.types),
  );
  const hasX4 = weakTo.some((a) => attackMultiplier(a, pokemon.types) >= 4);
  const immuneTo = TYPE_KEYS.filter((a) => attackMultiplier(a, pokemon.types) === 0);

  // 관장 상성: 추천 API(#25)로 관장마다 점수·평가·이유를 받습니다 (상대 파티 전체 기준, 서버 알고리즘).
  const leaders = trainers.filter((t) => t.category === "gym-leader");
  const recs = useApiAll<Recommendation>(
    leaders.map((t) => `/recommendations?pokemon_id=${pokemon.id}&trainer_id=${encodeURIComponent(t.id)}`),
  );
  const rated = recs.status === "ok" ? leaders.map((t, i) => ({ ...t, rec: recs.data[i] })) : [];
  const goodLeaders = rated.filter((t) => t.rec.rating === "good").sort((a, b) => b.rec.score - a.rec.score);
  const badLeaders = rated.filter((t) => t.rec.rating === "bad").sort((a, b) => a.rec.score - b.rec.score);
  const normalCount = rated.filter((t) => t.rec.rating === "normal").length;

  // 진화 관계는 API의 진화 계보(evolution_chain)에서 이 포켓몬의 앞·뒤 단계를 찾습니다.
  // 다음 진화가 여러 갈래면 첫 번째로 이동합니다.
  // evolution_chain이 null이면 아직 등록되지 않은 것이라 "다음 진화 없음"과 구분합니다.
  const evoUnknown = pokemon.evolution_chain == null;
  const chain = pokemon.evolution_chain ?? [];
  const prevId = chain.find((r) => r.to.id === pokemon.id)?.from.id;
  const nextEvo = chain.find((r) => r.from.id === pokemon.id);
  const nextId = nextEvo?.to.id;

  return (
    <DesignFrame>
      <DesignTopbar backTo="/pokemon" backLabel="포켓몬 정보" />
      <div className="dwrap">
        {/* 왼쪽: 도감 카드 */}
        <section className="panel dex">
          <div className="tab">
            <div className="no">
              <small>하나도감</small>
              {dexNumber(pokemon.id)}
            </div>
            <span className="region">하나지방</span>
          </div>
          <div className="body">
            <div className="dimg">
              <img src={artworkUrl(pokemon.id)} alt={pokemon.name} />
            </div>
            <div className="namerow">
              <h1>{pokemon.name}</h1>
              {pokemon.types.map((t) => (
                <span key={t} className={`type ${t}`} style={{ fontSize: 14, padding: "4px 16px" }}>
                  {typeLabel(t)}
                </span>
              ))}
            </div>
            <div className="facts">
              <div className="k">분류</div>
              <div className="v">연결 대기</div>
              <div className="k">특성</div>
              <div className="v">연결 대기</div>
              <div className="k">키</div>
              <div className="v">연결 대기</div>
              <div className="k">몸무게</div>
              <div className="v">연결 대기</div>
            </div>
            <button type="button" className="mapbtn" disabled={locations.length === 0} onClick={() => setMapOpen(true)}>
              <span className="pin" />
              맵보기
            </button>
            <div className="locs">
              <h3>출현 장소 · 시간대</h3>
              {locations.length === 0 && <p className="empty">출현 장소 데이터가 없습니다.</p>}
              {locations.map((place) => (
                <div key={place.id} className="loc">
                  {place.name}
                  <span className="chips">
                    <span className="chip">시간대 대기</span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 가운데 */}
        <div className="col">
          <section className="panel">
            <div className="ph">
              타입별 상성<span className="sub">{typeNames} 타입 기준</span>
            </div>
            <div className="pb" style={{ paddingTop: 6, paddingBottom: 6 }}>
              <div className="mrow">
                <span className="mlab adv">
                  유리 <b>×2</b>
                </span>
                {hits.length === 0 ? (
                  <span className="nonetxt">해당 없음</span>
                ) : (
                  <div className="types">
                    {hits.map((t) => (
                      <span key={t} className={`type ${t}`}>
                        {typeLabel(t)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="mrow">
                <span className="mlab half">
                  반감 <b>×0.5</b>
                </span>
                {resisted.length === 0 ? (
                  <span className="nonetxt">해당 없음</span>
                ) : (
                  <div className="types">
                    {resisted.map((t) => (
                      <span key={t} className={`type ${t}`}>
                        {typeLabel(t)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="mrow">
                <span className="mlab weak">
                  약점 <b>{hasX4 ? "×2~4" : "×2"}</b>
                </span>
                {weakTo.length === 0 ? (
                  <span className="nonetxt">해당 없음</span>
                ) : (
                  <div className="types">
                    {weakTo.map((t) => (
                      <span key={t} className={`type ${t}`}>
                        {typeLabel(t)}
                        {attackMultiplier(t, pokemon.types) >= 4 && <b className="x4">×4</b>}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="mrow">
                <span className="mlab zero">
                  효과X <b>×0</b>
                </span>
                {immuneTo.length === 0 ? (
                  <span className="nonetxt">해당 없음</span>
                ) : (
                  <>
                    <div className="types">
                      {immuneTo.map((t) => (
                        <span key={t} className={`type ${t}`}>
                          {typeLabel(t)}
                        </span>
                      ))}
                    </div>
                    <span className="mnote">{immuneTo.map(typeLabel).join(", ")} 기술이 통하지 않음</span>
                  </>
                )}
              </div>
            </div>
          </section>

          <section className="panel evo" style={{ flex: 1 }}>
            <div className="ph">
              진화 정보
              <span className="sub">
                {evoUnknown
                  ? "진화 정보 연결 대기"
                  : nextEvo
                    ? `다음 진화: ${nextEvo.to.name}${nextEvo.condition ? ` (${nextEvo.condition})` : ""}`
                    : "다음 진화 없음"}
              </span>
            </div>
            <div className="pb">
              <div className="dimg">
                <img src={bwAnimatedUrl(pokemon.id)} alt={pokemon.name} />
              </div>
              <div className="evname">{pokemon.name}</div>
              {prevId !== undefined && (
                <Link to={`/pokemon/${prevId}`} className="arrow prev" aria-label="이전 진화 포켓몬 보기" title="이전 진화">
                  <span className="tri-left" />
                </Link>
              )}
              {nextId !== undefined && (
                <Link to={`/pokemon/${nextId}`} className="arrow next" aria-label="다음 진화 포켓몬 보기" title="다음 진화">
                  <span className="tri" />
                </Link>
              )}
            </div>
          </section>
        </div>

        {/* 오른쪽 */}
        <div className="col">
          <section className="panel leaders">
            <div className="ph">관장 상성</div>
            <div className="pb">
              {recs.status !== "ok" ? (
                <StatusView status={recs.status} what="관장 상성" error={recs.error} onRetry={recs.retry} />
              ) : (
                <>
              <LeaderRow tag="좋음" cls="good" leaders={goodLeaders} />
              <div className="lsep" />
              <LeaderRow tag="나쁨" cls="bad" leaders={badLeaders} />
              <p className="lnote">
                보통 {normalCount}명 · 점수는 상대 파티 전체와의 타입 상성 기준(0~100)이며, 기술·레벨은 반영하지 않습니다.
              </p>
                </>
              )}
            </div>
          </section>

          <section className="panel moves" style={{ flex: 1 }}>
            <div className="ph">레벨별 추천 기술</div>
            <div className="pb">
              <p className="empty" style={{ gridColumn: "1 / -1" }}>
                기술 데이터 연결 대기
              </p>
            </div>
          </section>

          <section className="panel desc">
            <p>
              <b>포켓몬 설명</b>
              <span className="nonetxt">설명 데이터 연결 대기</span>
            </p>
          </section>
        </div>
      </div>

      {mapOpen && <MapPopover name={pokemon.name} places={locations} onClose={() => setMapOpen(false)} />}
    </DesignFrame>
  );
}

type RatedLeader = TrainerSummary & { rec: Recommendation };

/** 마우스를 올리면 보이는 설명: 서버가 만든 이유·주의점 */
function recTitle(t: RatedLeader): string {
  const lines = [`${t.name} · ${t.rec.rating_label} ${t.rec.score}점`, ...t.rec.reasons.map((r) => `+ ${r}`), ...t.rec.warnings.map((w) => `! ${w}`)];
  return lines.join("\n");
}

/** 관장 얼굴. 그림 파일이 없으면(저장소에서 제외됨) 이름 첫 글자 타일을 보여 줍니다. */
function LeaderFace({ id, name }: { id: string; name: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return (
      <span className="dsg-face-fallback" aria-hidden="true">
        {name.charAt(0)}
      </span>
    );
  }
  return <img src={trainerImageSrc(id, PORTRAIT_FORMAT)} alt="" onError={() => setFailed(true)} />;
}

function LeaderRow({ tag, cls, leaders }: { tag: string; cls: "good" | "bad"; leaders: RatedLeader[] }) {
  return (
    <div className={`lrow2 ${cls}`}>
      <span className="tag2">{tag}</span>
      {leaders.length === 0 ? (
        <span className="nonetxt">해당 없음</span>
      ) : (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {leaders.map((t) => (
            <div key={t.id} className="ld" style={{ width: 96 }} title={recTitle(t)}>
              <div className="face">
                <LeaderFace id={t.id} name={t.name} />
                <span className="score">{t.rec.score}</span>
              </div>
              <div className="namebox">{t.name}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
