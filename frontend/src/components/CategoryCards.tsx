import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { useNavigate } from "react-router-dom";

export interface CategoryCardItem {
  id: string;
  /** 카드 가운데 글씨. 줄바꿈은 \n으로 표시합니다. */
  label: string;
  path: string;
}

interface CategoryCardsProps {
  items: readonly CategoryCardItem[];
}

/**
 * 가로로 나란히 놓인 카테고리 카드 (트레이너 정보 첫 화면).
 * ← → 또는 A D로 옮기고 Enter로 고릅니다. 마우스로 올리면 선택이 따라옵니다.
 * 선택된 카드는 노란 테두리와 함께 살짝 커지고, 위에 ▼가 표시됩니다.
 */
export function CategoryCards({ items }: CategoryCardsProps) {
  const [cursor, setCursor] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    listRef.current?.focus();
  }, []);

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const key = event.key.toLowerCase();
    if (key === "arrowright" || key === "d") {
      event.preventDefault();
      setCursor((prev) => (prev + 1) % items.length);
    } else if (key === "arrowleft" || key === "a") {
      event.preventDefault();
      setCursor((prev) => (prev - 1 + items.length) % items.length);
    } else if (key === "enter") {
      event.preventDefault();
      navigate(items[cursor].path);
    }
  };

  return (
    <div
      ref={listRef}
      className="category-cards"
      role="listbox"
      aria-label="트레이너 카테고리"
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      {items.map((item, index) => {
        const selected = index === cursor;
        return (
          <div
            key={item.id}
            role="option"
            aria-selected={selected}
            className="category-card__slot"
            onMouseEnter={() => setCursor(index)}
            onClick={() => navigate(item.path)}
          >
            <span className={selected ? "category-card__pointer" : "category-card__pointer category-card__pointer--hidden"} aria-hidden="true">
              ▼
            </span>
            <div className={selected ? "category-card category-card--selected" : "category-card"}>
              <span className="category-card__label">{item.label}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
