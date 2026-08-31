import sys
import time
import math
import random
from rpi5_ws2812.ws2812 import Color
from led_common import LED_COUNT, get_strip

RATE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0

# My own invented asterism -- I'm calling it "The Wayfarer": an uneven
# zigzag of 7 stars meant to evoke a little figure walking across the sky.
# The spacing is deliberately irregular (like a real constellation) rather
# than evenly spaced, and it's expressed as fractions of the strip so it
# scales cleanly if LED_COUNT ever changes.
CONSTELLATION_FRACTIONS = [0.05, 0.16, 0.30, 0.34, 0.52, 0.71, 0.90]
CONSTELLATION = sorted(set(
    min(LED_COUNT - 1, int(round(f * (LED_COUNT - 1)))) for f in CONSTELLATION_FRACTIONS
))
CONSTELLATION_SET = set(CONSTELLATION)
CONSTELLATION_COLOR = (255, 195, 90)  # warm gold, so it reads apart from the background field

# Ordinary background stars: only some pixels get one (real night skies have
# gaps), each with its own twinkle speed, phase, peak brightness, and a
# color-temperature tint (real stars range from icy blue-white to warm amber).
STAR_DENSITY = 0.45
COOL_TINT = (150, 190, 255)
WARM_TINT = (255, 210, 150)
NEUTRAL_TINT = (200, 210, 255)


def tint_color(tint, brightness):
    brightness = max(0.0, min(1.0, brightness))
    return Color(int(tint[0] * brightness), int(tint[1] * brightness), int(tint[2] * brightness))


class BackgroundStar:
    def __init__(self):
        self.phase = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.5, 2.5)
        self.max_brightness = random.uniform(0.25, 1.0)
        self.tint = random.choice([COOL_TINT, WARM_TINT, NEUTRAL_TINT])

    def color(self, t):
        b = (math.sin(t * self.speed + self.phase) + 1) / 2
        b = b ** 2  # spend more time dim, punctuated by brighter flickers
        return tint_color(self.tint, b * self.max_brightness)


class ConstellationStar:
    def __init__(self):
        self.phase = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.15, 0.3)

    def color(self, t):
        b = 0.65 + 0.35 * ((math.sin(t * self.speed + self.phase) + 1) / 2)  # never goes fully dark
        return tint_color(CONSTELLATION_COLOR, b)


class ShootingStar:
    TRAIL = 5

    def __init__(self):
        self.birth = time.monotonic()
        self.direction = random.choice([1, -1])
        self.start = -self.TRAIL if self.direction == 1 else LED_COUNT - 1 + self.TRAIL
        self.speed = random.uniform(45.0, 70.0)

    def position(self, now):
        return self.start + self.direction * self.speed * (now - self.birth)

    def is_dead(self, now):
        pos = self.position(now)
        return pos < -self.TRAIL - 1 or pos > LED_COUNT + self.TRAIL

    def draw(self, strip, now):
        head = self.position(now)
        for offset in range(self.TRAIL + 1):
            idx = int(round(head)) - offset * self.direction
            if 0 <= idx < LED_COUNT:
                level = 1.0 - offset / self.TRAIL
                v = int(255 * level)
                strip.set_pixel_color(idx, Color(v, v, v))


def next_shooting_star_delay():
    return random.uniform(6.0, 14.0) / RATE


def main():
    strip = get_strip()

    constellation_stars = {i: ConstellationStar() for i in CONSTELLATION}

    available = [i for i in range(LED_COUNT) if i not in CONSTELLATION_SET]
    background_count = int(round(STAR_DENSITY * len(available)))
    background_indices = random.sample(available, min(background_count, len(available)))
    background_stars = {i: BackgroundStar() for i in background_indices}

    shooting_star = None
    shooting_timer = random.uniform(2.0, 6.0) / RATE

    last_time = time.monotonic()

    try:
        while True:
            now = time.monotonic()
            dt = now - last_time
            last_time = now

            shooting_timer -= dt
            if shooting_star is not None and shooting_star.is_dead(now):
                shooting_star = None
            if shooting_star is None and shooting_timer <= 0:
                shooting_star = ShootingStar()
                shooting_timer = next_shooting_star_delay()

            for i in range(LED_COUNT):
                if i in constellation_stars:
                    strip.set_pixel_color(i, constellation_stars[i].color(now))
                elif i in background_stars:
                    strip.set_pixel_color(i, background_stars[i].color(now))
                else:
                    strip.set_pixel_color(i, Color(0, 0, 0))

            if shooting_star is not None:
                shooting_star.draw(strip, now)

            strip.show()
            time.sleep(0.03)
    except KeyboardInterrupt:
        strip.clear()
        strip.show()


if __name__ == "__main__":
    main()
