import sys
import time
import math
import random
from rpi5_ws2812.ws2812 import Color
from led_common import LED_COUNT, get_strip

RATE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0

CALM_COLOR = (0, 40, 90)
PEAK_COLOR = (190, 225, 255)
CENTER = (LED_COUNT - 1) / 2.0


def water_color(intensity: float) -> Color:
    t = max(0.0, min(1.0, intensity))
    r = int(CALM_COLOR[0] + (PEAK_COLOR[0] - CALM_COLOR[0]) * t)
    g = int(CALM_COLOR[1] + (PEAK_COLOR[1] - CALM_COLOR[1]) * t)
    b = int(CALM_COLOR[2] + (PEAK_COLOR[2] - CALM_COLOR[2]) * t)
    return Color(r, g, b)


class Ripple:
    def __init__(self, origin, big):
        self.origin = origin
        self.birth = time.monotonic()
        self.big = big
        if big:
            self.amplitude = 1.0
            self.speed = random.uniform(5.0, 7.0)
            self.decay = 0.35
            self.width = random.uniform(2.5, 4.0)
        else:
            self.amplitude = 0.55
            self.speed = random.uniform(9.0, 13.0)
            self.decay = 0.9
            self.width = random.uniform(1.0, 2.0)

    def intensity_at(self, i, now):
        elapsed = now - self.birth
        radius = self.speed * elapsed
        distance = abs(i - self.origin)
        ring = math.exp(-((distance - radius) ** 2) / (2 * self.width ** 2))
        fade = math.exp(-self.decay * elapsed)
        return self.amplitude * ring * fade

    def is_dead(self, now, led_count):
        elapsed = now - self.birth
        radius = self.speed * elapsed
        fade = math.exp(-self.decay * elapsed)
        return (radius - self.width) > led_count or fade < 0.03


def spawn_interval():
    # big ripples are rarer, small ones more frequent
    return random.uniform(0.35, 1.1) / RATE


def main():
    strip = get_strip()
    ripples = []
    spawn_timer = 0.1
    last_time = time.monotonic()

    try:
        while True:
            now = time.monotonic()
            dt = now - last_time
            last_time = now

            spawn_timer -= dt
            if spawn_timer <= 0:
                big = random.random() < 0.3
                ripples.append(Ripple(CENTER, big))
                spawn_timer = spawn_interval()

            ripples = [r for r in ripples if not r.is_dead(now, LED_COUNT)]

            for i in range(LED_COUNT):
                intensity = 0.0
                for r in ripples:
                    intensity += r.intensity_at(i, now)
                strip.set_pixel_color(i, water_color(intensity))

            strip.show()
            time.sleep(0.02)
    except KeyboardInterrupt:
        strip.clear()
        strip.show()


if __name__ == "__main__":
    main()
