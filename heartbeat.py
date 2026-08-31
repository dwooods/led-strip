import math
import sys
import time
from rpi5_ws2812.ws2812 import Color
from led_common import LED_COUNT, get_strip

BPM = int(sys.argv[1]) if len(sys.argv) > 1 else 100


def main():
    strip = get_strip()
    center = (LED_COUNT - 1) / 2
    max_distance = max(center, LED_COUNT - 1 - center)
    cycle_length = 60.0 / BPM
    speed = (max_distance + 4) / (cycle_length * 0.6)
    ring_sigma = 1.5
    decay_rate = 3.0
    base_glow = 0.03

    pulses = []
    next_lub = time.monotonic()

    try:
        while True:
            now = time.monotonic()

            if now >= next_lub:
                pulses.append({"start": now, "amp": 1.0})
                pulses.append({"start": now + cycle_length * 0.16, "amp": 0.6})
                next_lub = now + cycle_length

            pulses = [p for p in pulses if (now - p["start"]) * speed < max_distance + 6]

            for i in range(LED_COUNT):
                d = abs(i - center)
                intensity = base_glow
                for p in pulses:
                    elapsed = now - p["start"]
                    if elapsed < 0:
                        continue
                    wavefront = elapsed * speed
                    ring = math.exp(-((d - wavefront) ** 2) / (2 * ring_sigma ** 2))
                    fade = math.exp(-elapsed * decay_rate)
                    intensity += p["amp"] * ring * fade
                intensity = min(intensity, 1.0)
                strip.set_pixel_color(i, Color(int(255 * intensity), 0, 0))

            strip.show()
            time.sleep(0.02)
    except KeyboardInterrupt:
        strip.clear()
        strip.show()


if __name__ == "__main__":
    main()
