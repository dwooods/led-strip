import random
import sys
import time
from rpi5_ws2812.ws2812 import Color
from led_common import LED_COUNT, get_strip

RATE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0

PALETTES = [
    (255, 60, 30),
    (255, 200, 40),
    (60, 140, 255),
    (80, 255, 120),
    (200, 80, 255),
    (255, 255, 255),
]

MIN_INTERVAL = 0.9 / RATE
MAX_INTERVAL = 2.2 / RATE


def scaled(color, intensity):
    intensity = max(0.0, min(intensity, 1.0))
    return Color(int(color[0] * intensity), int(color[1] * intensity), int(color[2] * intensity))


def spawn_rocket():
    target = random.uniform(LED_COUNT * 0.35, LED_COUNT * 0.95)
    return {
        "pos": 0.0,
        "target": target,
        "direction": 1,
        "speed": random.uniform(45, 65),
    }


def explode(rocket):
    color = random.choice(PALETTES)
    count = random.randint(10, 18)
    particles = []
    for _ in range(count):
        vel = random.uniform(-40, 40)
        if abs(vel) < 6:
            vel = 6 if vel >= 0 else -6
        particles.append({"pos": rocket["pos"], "vel": vel, "brightness": 1.0, "color": color})
    return particles


def main():
    strip = get_strip()
    rockets = []
    particles = []
    next_launch = time.monotonic()
    last_time = time.monotonic()

    try:
        while True:
            now = time.monotonic()
            dt = now - last_time
            last_time = now

            if now >= next_launch and len(rockets) == 0:
                rockets.append(spawn_rocket())
                next_launch = now + random.uniform(MIN_INTERVAL, MAX_INTERVAL)

            for rocket in rockets[:]:
                rocket["pos"] += rocket["direction"] * rocket["speed"] * dt
                reached = (rocket["direction"] > 0 and rocket["pos"] >= rocket["target"]) or \
                          (rocket["direction"] < 0 and rocket["pos"] <= rocket["target"])
                if reached:
                    particles.extend(explode(rocket))
                    rockets.remove(rocket)

            for p in particles[:]:
                p["vel"] *= (1 - 1.5 * dt)
                p["pos"] += p["vel"] * dt
                p["brightness"] -= dt * random.uniform(0.7, 1.1)
                if p["brightness"] <= 0.02 or p["pos"] < -2 or p["pos"] > LED_COUNT + 1:
                    particles.remove(p)

            for i in range(LED_COUNT):
                strip.set_pixel_color(i, Color(0, 0, 0))

            for rocket in rockets:
                idx = int(round(rocket["pos"]))
                if 0 <= idx < LED_COUNT:
                    strip.set_pixel_color(idx, Color(255, 220, 180))
                trail_idx = idx - rocket["direction"]
                if 0 <= trail_idx < LED_COUNT:
                    strip.set_pixel_color(trail_idx, Color(80, 60, 40))

            for p in particles:
                idx = int(round(p["pos"]))
                if 0 <= idx < LED_COUNT:
                    strip.set_pixel_color(idx, scaled(p["color"], p["brightness"]))

            strip.show()
            time.sleep(0.02)
    except KeyboardInterrupt:
        strip.clear()
        strip.show()


if __name__ == "__main__":
    main()
