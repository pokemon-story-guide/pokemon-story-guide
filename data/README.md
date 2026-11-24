# data

포켓몬스터 블랙/화이트 1 (5세대) 기준 데이터입니다.
포켓몬과 기술 데이터는 [PokeAPI](https://pokeapi.co)에서 내려받아 `scripts/build_data.py`로 변환해 만듭니다.

## 파일 구성

| `mon.json` | 하나 지방 포켓몬 (이름, 타입, 종족값 합계, 진화, 출현 장소, 사용 가능 여부) | PokeAPI + 수동 데이터(`encounters.json`) |
| `move.json` | 5세대의 기술 (이름, 타입, 기대 위력) | PokeAPI |
| `learn.json` | 각 포켓몬의 레벨업 기술 | PokeAPI |
| `place.json` | 장소 목록 | 수동 데이터 |
| `encounters.json` | 포켓몬별 출현 장소 ID (`mon.json`의 `location_ids`를 고칠 때는 이 파일을 수정) | 수동 데이터 |
| `scripts/build_data.py` | PokeAPI 호출 → JSON 생성 |
| `scripts/compare.py` | 두 폴더의 JSON 차이 비교 |

## 데이터 형식

### mon.json

5세대에 등장하는 포켓몬들에 대한 목록입니다.

| 필드 | 형식 | 설명 |
| `id` | int | 하나 지방 도감 번호 (0~155) |
| `name` | string | 한국어 이름 |
| `types` | string[] | 5세대 기준 영문 타입 1~2개 |
| `base_stats` | int[6] | 5세대 종족값. 순서: HP, 공격, 방어, 특수공격, 특수방어, 스피드 |
| `base_stat_total` | int | `base_stats`의 합계 |
| `location_ids` | int[] \| null | 출현 장소 ID (`place.json`). 야생 출현이 없으면 `null` |
| `evolution_from` | object[] \| null | 진화 전 포켓몬 `{id, name, condition}`. 없으면 `null` |
| `evolution_to` | object[] \| null | 진화 후 포켓몬 `{id, name, condition}`. 분기 진화는 여러 개. 없으면 `null` |
| `usable` | 0 \| 1 | 스토리 진행 중 사용 가능 여부. 전설·환상은 `0` |

진화 `condition`: 레벨이면 기존대로 숫자 문자열(`"17"`), 도구면 도구 이름(`"태양의돌"`), 그 외 `"통신"`, `"친밀도"`

### move.json

5세대에 등장하는 기술들에 대한 목록입니다.

| 필드 | 형식 | 설명 |
| `id` | int | 기술 번호 (1~559) |
| `name` | string | 한국어 이름 |
| `type` | string | 5세대 기준 영문 타입 |
| `expected_power` | int | 기대 위력. 변화기 `0`, 위력 변동·조건부 기술 `1` |

### learn.json

각 포켓몬이 레벨마다 배우는 기술들의 목록입니다.

| 필드 | 형식 | 설명 |
| `pokemon_id` | int | `mon.json`의 `id` |
| `moves` | object[] | 레벨업 기술 `{level, move_id}`. 레벨순 정렬 |

### encounters.json

`{"encounters": {"포켓몬 id": [장소 id, ...]}}` 형식입니다. 키는 문자열로 된 `mon.json`의 `id`입니다.

## 데이터 다시 만들기

```bash
# 1) 다른 폴더에 생성해서 현재 데이터와 비교
python data/scripts/build_data.py --out data/_test
python data/scripts/compare.py data data/_test

# 2) 확인이 끝나면 data/ 에 덮어쓰기
python data/scripts/build_data.py
```

- 처음 실행할 때 PokeAPI를 호출하며, 캐시 데이터가 없어서 좀 걸립니다.
- 응답은 `data/scripts/.cache/`에 저장되어 두 번째 실행부터는 바로 끝납니다.
- `data/_test/`는 확인용 폴더라서 커밋하지 않았습니다.

## 변환 규칙

- **번호**: `id`는 하나 지방 도감 번호입니다. '전국도감 번호 - 494'로 계산합니다. (155번까지입니다.)
- **이름**: PokeAPI의 한국어(`ko`) 이름
- **타입·종족값·기술 위력**: 이후 세대에서 바뀐 값은 `past_types`, `past_values` 등을 이용해 5세대 당시 값으로 되돌립니다.
- **진화 조건**: 레벨이면 숫자(`"17"`), 도구면 도구 이름(`"태양의 돌"`), 그 외 `"통신"`, `"친밀도"`
- **사용 가능 여부(`usable`)**: 전설·환상 포켓몬은 `0`, 나머지는 `1`
- **레벨업 기술**: 버전 그룹 `black-white`, 습득 방법 `level-up`
- **기대 위력(`expected_power`)**: `위력 × 명중률 × 최소 타격 횟수`를 반올림합니다. 단, 일부 기술은 아래 규칙을 따랐습니다.
  - 변화기는 0, 일격필살기와 위력이 정해지지 않은 기술은 1입니다.
  - 모으기 또는 반동으로 2턴이 걸리는 기술(솔라빔, 파괴광선 등)은 반토막냈습니다.
  - 사용 후 기절, 지연 공격, 조건부 기술, HP에 따라 위력이 줄어드는 기술은 1입니다.
  - 그 밖의 예외는 따로 처리했습니다.
- **기술 이름**: PokeAPI 한국어 이름을 쓰되, 잘못 들어간 이름은 `MOVE_NAME_OVERRIDES`로 고칩니다.
