import chooseUrl from "./data/sounds/choose_sound.mp3";

/** 메뉴를 골랐을 때 나는 소리 */
export const SOUND_CHOOSE = chooseUrl;

/** 방향키로 커서를 옮길 때 나는 소리. 지금은 선택음과 같은 파일이며, 이동음 파일이 생기면 여기만 바꿉니다. */
export const SOUND_MOVE = chooseUrl;

/** 전체 효과음 볼륨(0~1). 너무 크면 이 값을 낮춥니다. */
export const SOUND_VOLUME = 0.3;

const cache = new Map<string, HTMLAudioElement>();

/**
 * 효과음을 재생합니다. 같은 소리는 한 번만 만들어 두고 처음부터 다시 재생합니다.
 * 브라우저가 재생을 막거나 파일을 읽지 못해도 화면 동작은 그대로 이어집니다.
 */
export function playSound(url: string): void {
  try {
    let audio = cache.get(url);
    if (!audio) {
      audio = new Audio(url);
      cache.set(url, audio);
    }
    audio.volume = SOUND_VOLUME;
    audio.currentTime = 0;
    void audio.play().catch(() => {
      /* 사용자 입력 전이거나 재생이 막힌 경우: 조용히 넘어갑니다. */
    });
  } catch {
    /* 소리를 지원하지 않는 환경: 무시합니다. */
  }
}
