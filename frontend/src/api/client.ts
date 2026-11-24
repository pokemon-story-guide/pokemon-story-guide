import { useCallback, useEffect, useState } from "react";

/**
 * 백엔드 API 연결.
 * - 주소는 모두 `/api/...`이고, 개발·시연 서버(Vite)가 백엔드(기본 http://127.0.0.1:8000)로 넘겨 줍니다 (vite.config.ts의 proxy).
 * - 응답 모양은 백엔드 스키마(backend/api/schemas)를 그대로 따릅니다. 백엔드가 바뀌면 여기 타입만 맞추면 됩니다.
 */

/** 트레이너 분류 (백엔드 TrainerCategory) */
export type TrainerCategory = "gym-leader" | "elite-four" | "champion" | "plasma";

/** GET /api/trainers 항목 */
export interface TrainerSummary {
  id: string;
  name: string;
  category: TrainerCategory;
  type: string | null;
  badge_order: number | null;
  image: string;
}

/** 상대 파티 포켓몬 */
export interface PartyPokemon {
  pokemon_id: number;
  name: string;
  types: string[];
  level: number;
  image: string | null;
}

/** GET /api/trainers/{id} */
export interface TrainerDetail extends TrainerSummary {
  party: PartyPokemon[];
}

/** GET /api/pokemon 항목 */
export interface PokemonCard {
  id: number;
  name: string;
  types: string[];
  image: string | null;
}

export interface EvolutionPokemon {
  id: number;
  name: string;
}

/** 진화 관계 하나 (from → to) */
export interface EvolutionRelation {
  from: EvolutionPokemon;
  to: EvolutionPokemon;
  condition: string;
}

/** GET /api/pokemon/{id} */
export interface PokemonDetail extends PokemonCard {
  base_stat_total: number;
  /** null: 정보 미등록, []: 진화 관계 없음 */
  evolution_chain: EvolutionRelation[] | null;
}

/** GET /api/locations 항목, GET /api/pokemon/{id}/locations 항목 */
export interface Location {
  id: number;
  name: string;
}

/** GET /api/locations/{id}/pokemon 항목 */
export interface LocationPokemon {
  id: number;
  name: string;
  types: string[];
}

/** GET /api/recommendations?pokemon_id=&trainer_id= (포켓몬 1마리 vs 트레이너 1명 상성 평가, #25) */
export interface Recommendation {
  pokemon_id: number;
  trainer_id: string;
  /** 0~100점 (승률 아님) */
  score: number;
  rating: "good" | "normal" | "bad";
  rating_label: "좋음" | "보통" | "나쁨";
  /** 유리한 이유 (없으면 빈 목록) */
  reasons: string[];
  /** 주의할 점 (없으면 빈 목록) */
  warnings: string[];
  evaluation_basis: string;
}

/** 응답 오류. status 404는 "정보 없음", 그 외는 "서버 오류"로 보여 줍니다. */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

/** 같은 주소는 한 번만 불러와서 화면끼리 함께 씁니다 (실패하면 다음에 다시 시도). */
const cache = new Map<string, Promise<unknown>>();

export function apiGet<T>(path: string): Promise<T> {
  const hit = cache.get(path);
  if (hit) return hit as Promise<T>;
  const request = fetch(`/api${path}`, { headers: { Accept: "application/json" } })
    .then(async (res) => {
      if (!res.ok) throw new ApiError(res.status, `${res.status} ${res.statusText}`);
      return (await res.json()) as T;
    })
    .catch((err: unknown) => {
      cache.delete(path);
      throw err instanceof ApiError ? err : new ApiError(0, "서버에 연결하지 못했습니다");
    });
  cache.set(path, request);
  return request;
}

export type ApiState<T> =
  | { status: "loading"; data?: undefined; error?: undefined }
  | { status: "ok"; data: T; error?: undefined }
  | { status: "error"; data?: undefined; error: ApiError };

/**
 * 화면에서 API를 부르는 훅. path가 null이면 부르지 않습니다.
 * retry()로 다시 불러옵니다.
 */
export function useApi<T>(path: string | null): ApiState<T> & { retry: () => void } {
  // 결과에 어느 주소의 결과인지 함께 적어 둡니다. 주소가 바뀐 직후에는 예전 결과를 쓰지 않고 '불러오는 중'으로 봅니다.
  const [state, setState] = useState<{ key: string | null; value: ApiState<T> }>({ key: null, value: { status: "loading" } });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (path === null) return;
    let alive = true;
    setState({ key: path, value: { status: "loading" } });
    apiGet<T>(path).then(
      (data) => alive && setState({ key: path, value: { status: "ok", data } }),
      (error: ApiError) => alive && setState({ key: path, value: { status: "error", error } }),
    );
    return () => {
      alive = false;
    };
  }, [path, attempt]);

  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  const value: ApiState<T> = state.key === path ? state.value : { status: "loading" };
  return { ...value, retry };
}

/** 여러 주소를 한꺼번에 불러옵니다 (모두 받으면 ok, 하나라도 실패하면 error). */
export function useApiAll<T>(paths: readonly string[]): ApiState<T[]> & { retry: () => void } {
  const key = paths.join("|");
  // 주소 목록이 바뀐 직후에는 예전 결과(개수가 다를 수 있음)를 쓰지 않고 '불러오는 중'으로 봅니다.
  const [state, setState] = useState<{ key: string | null; value: ApiState<T[]> }>({ key: null, value: { status: "loading" } });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let alive = true;
    setState({ key, value: { status: "loading" } });
    Promise.all(key.split("|").filter(Boolean).map((p) => apiGet<T>(p))).then(
      (data) => alive && setState({ key, value: { status: "ok", data } }),
      (error: ApiError) => alive && setState({ key, value: { status: "error", error } }),
    );
    return () => {
      alive = false;
    };
  }, [key, attempt]);

  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  const value: ApiState<T[]> = state.key === key ? state.value : { status: "loading" };
  return { ...value, retry };
}

/** 여러 API 상태를 하나로 합칩니다 (하나라도 오류면 오류, 하나라도 불러오는 중이면 불러오는 중). */
export function combineStatus(...states: { status: ApiState<unknown>["status"]; error?: ApiError }[]) {
  const failed = states.find((s) => s.status === "error");
  if (failed) return { status: "error" as const, error: failed.error as ApiError };
  if (states.some((s) => s.status === "loading")) return { status: "loading" as const };
  return { status: "ok" as const };
}

/** 트레이너 목록을 id로 찾기 쉽게 바꿉니다. */
export function byId<T extends { id: string }>(list: readonly T[]): Record<string, T> {
  return Object.fromEntries(list.map((t) => [t.id, t]));
}
