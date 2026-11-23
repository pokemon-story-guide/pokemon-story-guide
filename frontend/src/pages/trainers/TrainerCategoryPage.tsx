import { Link } from "react-router-dom";
import { CategoryCards, type CategoryCardItem } from "../../components/CategoryCards";

const CATEGORY_CARDS: readonly CategoryCardItem[] = [
  { id: "gym", label: "관장", path: "/trainers/gym" },
  { id: "elite", label: "사천왕 및\n챔피언", path: "/trainers/elite" },
  { id: "plasma", label: "플라스마단", path: "/trainers/plasma" },
];

/**
 * 트레이너 정보 첫 화면: 관장 / 사천왕 및 챔피언 / 플라스마단 카드 3개.
 * 제목은 왼쪽 위, "메인으로"는 오른쪽 아래에 둡니다.
 */
export function TrainerCategoryPage() {
  return (
    <div className="trainer-page">
      <div className="trainer-categories">
        <p className="trainer-categories__title">트레이너 정보</p>

        <div className="trainer-categories__body">
          <section className="trainer-popup">
            <CategoryCards items={CATEGORY_CARDS} />
          </section>
        </div>

        <div className="trainer-categories__footer">
          <Link to="/" className="return-icon" aria-label="메인으로" title="메인으로">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M3 12a9 9 0 1 0 3-6.7" />
              <path d="M3 4v5h5" />
            </svg>
          </Link>
        </div>
      </div>
    </div>
  );
}
