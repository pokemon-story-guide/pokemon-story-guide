from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 사용자가 고를 수 있는 게임 버전입니다.
GameVersion = Literal["black", "white"]


class Progress(BaseModel):
    """트레이너 화면의 진행 상태입니다. 보내지 않은 값은 처음 상태(기본값)로 저장됩니다."""

    # 정해지지 않은 칸(오타 포함)이 들어오면 저장하지 않고 422로 돌려보냅니다.
    model_config = ConfigDict(extra="forbid")

    version: GameVersion | None = Field(
        default=None,
        description="고른 게임 버전. `black` 또는 `white`이며, 아직 고르지 않았으면 `null`입니다.",
        examples=["black"],
    )
    gym_unlocked: int = Field(
        default=1,
        ge=1,
        le=8,
        description="열린 체육관 수(1~8). 처음에는 1번 체육관만 열려 있습니다.",
        examples=[4],
    )
    champion_unlocked: bool = Field(
        default=False,
        description="챔피언이 열렸는지 여부.",
        examples=[False],
    )
    n_story_cleared: int = Field(
        default=0,
        ge=0,
        le=6,
        description="깬 N 스토리 수(0~6). 버전을 고르면 N 스토리는 5개입니다.",
        examples=[2],
    )


class ProgressUpdate(BaseModel):
    """바꿀 값만 보내는 진행 상태입니다. 보내지 않은 값은 저장된 값을 그대로 둡니다."""

    model_config = ConfigDict(extra="forbid")

    version: GameVersion | None = Field(
        default=None,
        description="고른 게임 버전. `null`을 보내면 고르지 않은 상태로 바뀝니다.",
        examples=["black"],
    )
    gym_unlocked: int | None = Field(default=None, ge=1, le=8, description="열린 체육관 수(1~8).", examples=[5])
    champion_unlocked: bool | None = Field(default=None, description="챔피언이 열렸는지 여부.", examples=[True])
    n_story_cleared: int | None = Field(default=None, ge=0, le=6, description="깬 N 스토리 수(0~6).", examples=[3])

    @field_validator("gym_unlocked", "champion_unlocked", "n_story_cleared")
    @classmethod
    def _reject_null(cls, value):
        # 바꾸지 않을 값은 null 대신 빼고 보내야 합니다.
        if value is None:
            raise ValueError("null은 보낼 수 없습니다. 바꾸지 않을 값은 빼고 보내 주세요.")
        return value
