import sys
import time
import math
import random
from rpi5_ws2812.ws2812 import Color
from led_common import LED_COUNT, get_strip

SPEED = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0

ROCKET_COLOR = Color(255, 255, 255)
TRAIL_LENGTH = 8
NUM_STARS = max(3, LED_COUNT // 8)


def heat_color(heat: int) -> Color:
    heat = max(0, min(255, heat))
    t192 = round((heat / 255.0) * 191)
    heatramp = (t192 & 0x3F) << 2
    if t192 & 0x80:
        return Color(255, 255, heatramp)
    elif t192 & 0x40:
        return Color(255, heatramp, 0)
    else:
        return Color(heatramp, 0, 0)


class Star:
    def __init__(self, index):
        self.index = index
        self.phase = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(1.5, 4.0)
        self.max_brightness = random.uniform(0.15, 0.5)

    def color(self, t):
        b = (math.sin(t * self.speed + self.phase) + 1) / 2  # 0..1
        level = int(self.max_brightness * b * 255)
        return Color(level, level, level)


def make_stars():
    indices = random.sample(range(LED_COUNT), min(NUM_STARS, LED_COUNT))
    return [Star(i) for i in indices]


def main():
    strip = get_strip()
    pos = 0.0
    speed = 8.0 * SPEED
    acceleration = 14.0 * SPEED
    pause_frames = 0
    last_time = time.monotonic()
    elapsed = 0.0
    stars = make_stars()

    try:
        while True:
            now = time.monotonic()
            dt = now - last_time
            last_time = now
            elapsed += dt

            if pause_frames > 0:
                pause_frames -= 1
            else:
                speed += acceleration * dt
                pos += speed * dt
                if pos >= LED_COUNT + TRAIL_LENGTH:
                    pos = 0.0
                    speed = 8.0 * SPEED
                    pause_frames = 25
                    stars = make_stars()

            # starfield background — twinkling dim pixels standing in for space
            for i in range(LED_COUNT):
                strip.set_pixel_color(i, Color(0, 0, 0))
            for star in stars:
                strip.set_pixel_color(star.index, star.color(elapsed))

            nose_idx = int(round(pos))
            if 0 <= nose_idx < LED_COUNT:
                strip.set_pixel_color(nose_idx, ROCKET_COLOR)

            if pause_frames == 0:
                for step in range(1, TRAIL_LENGTH + 1):
                    trail_idx = nose_idx - step
                    if 0 <= trail_idx < LED_COUNT:
                        heat = int(255 * (1 - step / TRAIL_LENGTH))
                        strip.set_pixel_color(trail_idx, heat_color(heat))

            strip.show()
            time.sleep(0.02)
    except KeyboardInterrupt:
        strip.clear()
        strip.show()


if __name__ == "__main__":
    main()
