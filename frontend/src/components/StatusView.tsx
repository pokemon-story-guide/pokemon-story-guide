import type { ApiError } from "../api/client";

/**
 * 공통 상태 화면 (사용자 시안): 불러오는 중 / 정보 없음 / 오류를 서로 다르게 보여 줍니다.
 * - 불러오는 중: 스피너 + "○○ 정보를 불러오는 중…"
 * - 정보 없음(404): ⊘ + "해당 ○○ 정보를 찾을 수 없습니다", 다시 시도 없음
 * - 오류: ! + "정보를 불러오지 못했어요" + [다시 시도]
 */
export function StatusView({
  status,
  what,
  error,
  onRetry,
}: {
  status: "loading" | "error";
  /** 무엇을 불러오는지 (예: "포켓몬", "트레이너") */
  what: string;
  error?: ApiError;
  onRetry?: () => void;
}) {
  if (status === "loading") {
    return (
      <div className="status-view" role="status">
        <span className="spinner" aria-hidden="true" />
        <p>{what} 정보를 불러오는 중…</p>
      </div>
    );
  }
  if (error?.status === 404) {
    return (
      <div className="status-view">
        <span className="sicon none" aria-hidden="true">⊘</span>
        <p>해당 {what} 정보를 찾을 수 없습니다</p>
        <small>(빈 결과)</small>
      </div>
    );
  }
  return (
    <div className="status-view" role="alert">
      <span className="sicon err" aria-hidden="true">!</span>
      <p>정보를 불러오지 못했어요</p>
      {onRetry && (
        <button type="button" className="retry" onClick={onRetry}>
          다시 시도
        </button>
      )}
      <small>서버 오류{error?.status ? ` (${error.status})` : " · 백엔드 서버가 켜져 있는지 확인해 주세요"}</small>
    </div>
  );
}
