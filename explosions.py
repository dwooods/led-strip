import random
import sys
import time
from rpi5_ws2812.ws2812 import Color
from led_common import LED_COUNT, get_strip

RATE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
MIN_INTERVAL = 0.5 / RATE
MAX_INTERVAL = 1.6 / RATE


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


def spawn_explosion(particles, flashes):
    center = random.uniform(3, LED_COUNT - 4)
    count = random.randint(14, 24)
    for _ in range(count):
        vel = random.uniform(-55, 55)
        if abs(vel) < 8:
            vel = 8 if vel >= 0 else -8
        particles.append({"pos": center, "vel": vel, "heat": 255.0})
    flashes.append({"center": center, "start": time.monotonic()})


def main():
    strip = get_strip()
    particles = []
    flashes = []
    next_blast = time.monotonic() + random.uniform(0.2, 1.0)
    last_time = time.monotonic()

    try:
        while True:
            now = time.monotonic()
            dt = now - last_time
            last_time = now

            if now >= next_blast:
                spawn_explosion(particles, flashes)
                next_blast = now + random.uniform(MIN_INTERVAL, MAX_INTERVAL)

            for p in particles[:]:
                p["vel"] *= (1 - 2.0 * dt)
                p["pos"] += p["vel"] * dt
                p["heat"] -= dt * random.uniform(320, 420)
                if p["heat"] <= 0 or p["pos"] < -2 or p["pos"] > LED_COUNT + 1:
                    particles.remove(p)

            flashes[:] = [f for f in flashes if now - f["start"] < 0.05]

            for i in range(LED_COUNT):
                strip.set_pixel_color(i, Color(0, 0, 0))

            for p in particles:
                idx = int(round(p["pos"]))
                if 0 <= idx < LED_COUNT:
                    strip.set_pixel_color(idx, heat_color(int(p["heat"])))

            for f in flashes:
                center_idx = int(round(f["center"]))
                for offset in (-1, 0, 1):
                    idx = center_idx + offset
                    if 0 <= idx < LED_COUNT:
                        strip.set_pixel_color(idx, Color(255, 255, 255))

            strip.show()
            time.sleep(0.02)
    except KeyboardInterrupt:
        strip.clear()
        strip.show()


if __name__ == "__main__":
    main()
