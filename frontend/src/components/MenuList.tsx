import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import type { MenuItem } from "../config/menuItems";
import { playSound, SOUND_CHOOSE, SOUND_MOVE } from "../sound";

interface MenuListProps {
  items: readonly MenuItem[];
  onSelect: (item: MenuItem) => void;
}

/**
 * 키보드(↑ ↓ 또는 W S, Enter)와 마우스로 고를 수 있는 메뉴 목록.
 * 화면이 열리면 자동으로 포커스를 받아, 별도 클릭 없이 키로 고를 수 있습니다.
 * 포켓로그식 커서 메뉴의 동작을 우리 코드로 새로 구현한 것입니다.
 */
export function MenuList({ items, onSelect }: MenuListProps) {
  const [cursor, setCursor] = useState(0);
  const listRef = useRef<HTMLDivElement>(null);

  /** 고를 때(Enter 또는 클릭) 소리를 내고 선택을 알립니다. */
  const choose = (item: MenuItem) => {
    playSound(SOUND_CHOOSE);
    onSelect(item);
  };

  useEffect(() => {
    listRef.current?.focus();
  }, []);

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const key = event.key.toLowerCase();
    if (key === "arrowdown" || key === "s") {
      event.preventDefault();
      playSound(SOUND_MOVE);
      setCursor((prev) => (prev + 1) % items.length);
    } else if (key === "arrowup" || key === "w") {
      event.preventDefault();
      playSound(SOUND_MOVE);
      setCursor((prev) => (prev - 1 + items.length) % items.length);
    } else if (key === "enter") {
      event.preventDefault();
      choose(items[cursor]);
    }
  };

  return (
    <div
      ref={listRef}
      className="menu-list"
      role="listbox"
      aria-label="메인 메뉴"
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
            className={selected ? "menu-item menu-item--selected" : "menu-item"}
            onMouseEnter={() => setCursor(index)}
            onClick={() => choose(item)}
          >
            <span className="menu-item__cursor" aria-hidden="true">
              {selected ? "▶" : ""}
            </span>
            <span className="menu-item__body">
              <span className="menu-item__label">{item.label}</span>
              <span className="menu-item__desc">{item.description}</span>
            </span>
          </div>
        );
      })}
    </div>
  );
}
