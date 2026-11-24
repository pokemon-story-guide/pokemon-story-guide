from typing import Literal

from pydantic import BaseModel, Field

from api.schemas.pokemon import PokemonType


class OverallOpponentEvaluation(BaseModel):
    id: str = Field(description="상대 트레이너 ID.")
    name: str = Field(description="상대 트레이너의 한글 이름.")
    score: int = Field(ge=0, le=100, description="이 트레이너의 파티 상대 상성 점수.")
    rating: Literal["good", "normal", "bad"] = Field(description="개별 상대에 대한 평가 코드.")
    rating_label: Literal["좋음", "보통", "나쁨"] = Field(description="개별 상대에 대한 한글 평가.")


class OverallGroupEvaluation(BaseModel):
    group: str = Field(description="평가 그룹 ID. 체육관은 gym-{순서}, 나머지는 트레이너 ID입니다.")
    group_name: str = Field(description="표시용 그룹 이름. 예: 4번째 체육관, 카틀레야.")
    category: str = Field(description="상대 분류: gym-leader, elite-four, champion, plasma.")
    score: float = Field(ge=0, le=100, description="그룹 내 트레이너 점수의 평균. 소수점 첫째 자리까지 반올림합니다.")
    weight: float = Field(gt=0, description="전체 점수 계산에 적용한 그룹 비중. 현재 모두 1입니다.")
    opponents: list[OverallOpponentEvaluation] = Field(min_length=1, description="이 그룹에 포함된 개별 트레이너의 평가 목록.")


class OverallRecommendationSummary(BaseModel):
    group_count: int = Field(ge=1, description="전체 평가에 포함된 그룹 수. 체육관은 한 그룹으로 계산합니다.")
    good_count: int = Field(ge=0, description="그룹 평균을 정수로 반올림한 평가가 좋음인 그룹 수.")
    bad_count: int = Field(ge=0, description="그룹 평균을 정수로 반올림한 평가가 나쁨인 그룹 수.")
    best_group: str = Field(description="최고 점수 그룹 ID. details의 group과 연결합니다. 동점은 기존 알고리즘의 마지막 그룹입니다.")
    worst_group: str = Field(description="최저 점수 그룹 ID. details의 group과 연결합니다. 동점은 기존 알고리즘의 첫 그룹입니다.")


class OverallRecommendation(BaseModel):
    pokemon_id: int = Field(ge=0, description="선택한 포켓몬의 하나도감 ID. 전국도감 번호와 다릅니다.")
    name: str = Field(description="선택한 포켓몬의 한글 이름.")
    types: list[PokemonType] = Field(min_length=1, max_length=2, description="선택한 포켓몬의 영문 타입 목록.")
    score: int = Field(ge=0, le=100, description="주요 상대 그룹별 점수의 가중 평균을 정수로 반올림한 전체 점수. 승률이 아닙니다.")
    rating: Literal["good", "normal", "bad"] = Field(description="전체 평가 코드.")
    rating_label: Literal["좋음", "보통", "나쁨"] = Field(description="전체 점수의 한글 평가.")
    summary: OverallRecommendationSummary = Field(description="평가 그룹 수와 최고·최저 점수 그룹 요약.")
    explanation: str = Field(description="전체 점수와 상대적으로 높은·낮은 그룹을 설명하는 한국어 문장.")
    details: list[OverallGroupEvaluation] = Field(min_length=1, description="그룹별 점수·비중과 개별 상대 평가. 트레이너 데이터 순서입니다.")
    evaluation_basis: str = Field(description="포함·제외한 상대, 평균 계산 방식, 반영하지 않은 정보 안내.")
