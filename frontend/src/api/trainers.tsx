import type { ReactNode } from "react";
import { StatusView } from "../components/StatusView";
import { forVersion, PLASMA_GHETSIS_ID } from "../config/trainerGroups";
import { byId, useApi, type TrainerSummary } from "./client";

/**
 * 트레이너 목록 API(GET /api/trainers)와 화면용 묶음.
 * 묶음 기준은 서버 데이터를 따릅니다.
 * - 관장: badge_order(1~8)로 체육관을 나눔 (같은 번호 = 같은 체육관)
 * - 사천왕·챔피언·플라스마단: category, 순서는 API가 준 순서
 * - 버전 전용 인물(8번 관장, N의 성)은 고른 버전만 남김 (forVersion)
 */
export interface TrainerGroups {
  /** id → 트레이너 */
  byId: Record<string, TrainerSummary>;
  /** 체육관 번호(1~8) → 관장 목록 */
  gym: (badge: number) => TrainerSummary[];
  eliteFour: TrainerSummary[];
  champion: TrainerSummary | undefined;
  ghetsis: TrainerSummary | undefined;
  /** N (스토리 순서) */
  nStory: TrainerSummary[];
}

export function groupTrainers(list: readonly TrainerSummary[]): TrainerGroups {
  const visible = new Set(forVersion(list.map((t) => t.id)));
  const shown = list.filter((t) => visible.has(t.id));
  return {
    byId: byId(list),
    gym: (badge) => shown.filter((t) => t.category === "gym-leader" && t.badge_order === badge),
    eliteFour: shown.filter((t) => t.category === "elite-four"),
    champion: shown.find((t) => t.category === "champion"),
    ghetsis: shown.find((t) => t.id === PLASMA_GHETSIS_ID),
    nStory: shown.filter((t) => t.category === "plasma" && t.id !== PLASMA_GHETSIS_ID),
  };
}

/** 트레이너 목록을 불러옵니다 (여러 화면이 함께 써도 한 번만 요청). */
export function useTrainers() {
  const state = useApi<TrainerSummary[]>("/trainers");
  return { ...state, groups: state.status === "ok" ? groupTrainers(state.data) : undefined };
}

/**
 * 트레이너 목록이 있어야 그릴 수 있는 화면을 감쌉니다.
 * 불러오는 중·오류면 화면 가득 상태 화면을 보여 줍니다.
 */
export function TrainersGate({ children }: { children: (groups: TrainerGroups) => ReactNode }) {
  const { status, groups, error, retry } = useTrainers();
  if (status !== "ok" || !groups) {
    return (
      <div className="status-page">
        <section className="panel">
          <StatusView status={status === "ok" ? "loading" : status} what="트레이너" error={error} onRetry={retry} />
        </section>
      </div>
    );
  }
  return <>{children(groups)}</>;
}
