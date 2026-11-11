from pydantic import BaseModel, Field


class Location(BaseModel):
    id: int = Field(description="장소 목록·포켓몬 등장 위치·지도 연결에서 공통으로 사용하는 장소 ID.", examples=[0])
    name: str = Field(description="장소의 한글 이름.", examples=["리버티가든섬"])


class LocationPokemon(BaseModel):
    id: int = Field(description="데이터의 하나도감 기준 포켓몬 ID. 전국도감 번호와 다릅니다.", examples=[0])
    name: str = Field(description="포켓몬의 한글 이름.", examples=["비크티니"])
    types: list[str] = Field(
        description="포켓몬의 영문 타입 목록. 복합 타입은 두 항목을 반환합니다.",
        examples=[["psychic", "fire"]],
    )
