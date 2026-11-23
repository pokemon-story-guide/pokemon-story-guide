import { useState } from "react";
import { Link } from "react-router-dom";


interface TrainerCardProps {
  /** 이미지 파일 이름 (예: "shauntal" → /trainer-images/shauntal.webp) */
  imageId: string;
  name: string;
  subtitle?: string;
  to: string;
}

/**
 * 인물 카드 (사천왕, 관장 등 목록용).
 * 이미지 파일이 없으면 이름 첫 글자 타일을 대신 보여 줍니다.
 * 디자인은 시연 후 조정합니다.
 */
export function TrainerCard({ imageId, name, subtitle, to }: TrainerCardProps) {
  const [imageFailed, setImageFailed] = useState(false);
  const src = `/trainer-images/${imageId}.webp`;

  return (
    <Link to={to} className="trainer-card">
      <span className="trainer-card__image">
        {imageFailed ? (
          <span className="trainer-card__fallback" aria-hidden="true">
            {name.charAt(0)}
          </span>
        ) : (
          <img src={src} alt="" onError={() => setImageFailed(true)} />
        )}
      </span>
      <span className="trainer-card__name">{name}</span>
      {subtitle && <span className="trainer-card__sub">{subtitle}</span>}
    </Link>
  );
}
