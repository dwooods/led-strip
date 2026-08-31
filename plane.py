import sys
import time
from rpi5_ws2812.ws2812 import Color
from led_common import LED_COUNT, get_strip

SPEED = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0

CRUISE_SPEED = 14.0 * SPEED  # pixels/sec, constant -- planes cruise, they don't accelerate like the rocket
CONTRAIL_LENGTH = 6
TOTAL_LENGTH = 3 + CONTRAIL_LENGTH  # nose + green nav light + red nav light + fading contrail
PAUSE_SECONDS = 1.5

WHITE = (255, 255, 255)
GREEN_NAV = (40, 200, 60)
RED_NAV = (200, 30, 30)
STROBE_PERIOD = 1.4
STROBE_ON_TIME = 0.12


def body_color(offset, now):
    # offset 0 = nose, counting backward along the direction of travel
    if offset == 0:
        return Color(*WHITE)
    if offset == 1:
        if (now % STROBE_PERIOD) < STROBE_ON_TIME:
            return Color(255, 255, 255)  # anti-collision strobe flash
        return Color(*GREEN_NAV)
    if offset == 2:
        return Color(*RED_NAV)
    if offset <= 2 + CONTRAIL_LENGTH:
        t = (offset - 2) / CONTRAIL_LENGTH
        level = int(110 * (1 - t))
        return Color(level, level, level)
    return None


def main():
    strip = get_strip()
    direction = 1
    position = -TOTAL_LENGTH
    pause_timer = 0.0
    last_time = time.monotonic()

    try:
        while True:
            now = time.monotonic()
            dt = now - last_time
            last_time = now

            if pause_timer > 0:
                pause_timer -= dt
            else:
                position += direction * CRUISE_SPEED * dt
                nose = position
                if nose > LED_COUNT - 1 + TOTAL_LENGTH or nose < -TOTAL_LENGTH:
                    direction *= -1
                    position = -TOTAL_LENGTH if direction == 1 else LED_COUNT - 1 + TOTAL_LENGTH
                    pause_timer = PAUSE_SECONDS

            for i in range(LED_COUNT):
                strip.set_pixel_color(i, Color(0, 0, 0))

            if pause_timer <= 0:
                nose_idx = int(round(position))
                for offset in range(TOTAL_LENGTH + 1):
                    idx = nose_idx - offset * direction
                    if 0 <= idx < LED_COUNT:
                        color = body_color(offset, now)
                        if color is not None:
                            strip.set_pixel_color(idx, color)

            strip.show()
            time.sleep(0.02)
    except KeyboardInterrupt:
        strip.clear()
        strip.show()


if __name__ == "__main__":
    main()
