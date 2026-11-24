import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { DesignFrame, DesignTopbar } from "../components/DesignFrame";
import { useApi, type PokemonCard } from "../api/client";
import { StatusView } from "../components/StatusView";
import { artworkUrl, dexNumber, matchesQuery, TYPE_KEYS, typeLabel } from "../lib/pokemon";

/**
 * 포켓몬 정보 목록 (목업 search 구성). 포켓몬 API(GET /api/pokemon)의 하나도감 목록을 도감 번호순으로 보여 줍니다.
 * - 목록은 한 번 받아 두고, 초성 검색이 되도록 화면에서 거릅니다.
 * - 검색: 이름 또는 초성 (예: 깜눈크, ㄲㄴㅋ)
 * - 타입 필터: 한 타입을 고르면 그 타입이 있는 포켓몬만 보입니다.
 * - 카드를 누르면 포켓몬 상세로 갑니다.
 */
export function PokemonSearchPage() {
  const [query, setQuery] = useState("");
  const [type, setType] = useState("");

  const api = useApi<PokemonCard[]>("/pokemon");
  const list = useMemo(
    () => (api.data ?? []).filter((p) => (type === "" || p.types.includes(type)) && matchesQuery(p.name, query)),
    [api.data, query, type],
  );

  return (
    <DesignFrame>
      <DesignTopbar backTo="/" backLabel="메인" />
      <div className="mapwrap">
        <section className="panel list" style={{ flex: 1 }}>
          <div className="sbar">
            <label className="sbox">
              <span className="q">
                <i />
              </span>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="포켓몬 이름이나 초성으로 검색 (예: 깜눈크, ㄲㄴㅋ)"
                aria-label="포켓몬 검색"
              />
            </label>
            <div className="filter">
              <select value={type} onChange={(e) => setType(e.target.value)} aria-label="타입 필터">
                <option value="">타입 전체</option>
                {TYPE_KEYS.map((t) => (
                  <option key={t} value={t}>
                    {typeLabel(t)}
                  </option>
                ))}
              </select>
              <span className="chev" />
            </div>
          </div>
          <div className="meta">
            하나도감<b>{list.length}</b>마리<span className="sort">도감 번호순</span>
          </div>
          <div className="area">
            <div className="scroll">
              {api.status !== "ok" ? (
                <StatusView status={api.status} what="포켓몬" error={api.error} onRetry={api.retry} />
              ) : list.length === 0 ? (
                <p className="empty" style={{ margin: "40px 0" }}>
                  검색 결과가 없습니다.
                </p>
              ) : (
                <div className="grid">
                  {list.map((p) => (
                    <Link key={p.id} to={`/pokemon/${p.id}`} className="card">
                      <div className="ctab">
                        <span className="no">{dexNumber(p.id)}</span>
                        <b>{p.name}</b>
                      </div>
                      <div className="cimg">
                        <img src={artworkUrl(p.id)} alt="" loading="lazy" />
                      </div>
                      <div className="ctypes">
                        {p.types.map((t) => (
                          <span key={t} className={`type ${t}`}>
                            {typeLabel(t)}
                          </span>
                        ))}
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
            <div className="fade" />
          </div>
        </section>
      </div>
    </DesignFrame>
  );
}
