import random
import sys
import time
from rpi5_ws2812.ws2812 import Color
from led_common import LED_COUNT, get_strip

INTENSITY = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
SPARKING = max(0, min(255, int(120 * INTENSITY)))
COOLING = max(20, min(100, int(55 / max(INTENSITY, 0.2))))


def heat_color(heat: int) -> Color:
    t192 = round((heat / 255.0) * 191)
    heatramp = (t192 & 0x3F) << 2
    if t192 & 0x80:
        return Color(255, 255, heatramp)
    elif t192 & 0x40:
        return Color(255, heatramp, 0)
    else:
        return Color(heatramp, 0, 0)


def main():
    strip = get_strip()
    heat = [0] * LED_COUNT

    try:
        while True:
            for i in range(LED_COUNT):
                cooldown = random.randint(0, ((COOLING * 10) // LED_COUNT) + 2)
                heat[i] = max(0, heat[i] - cooldown)

            for i in range(LED_COUNT - 1, 1, -1):
                heat[i] = (heat[i - 1] + heat[i - 2] + heat[i - 2]) // 3

            if random.randint(0, 255) < SPARKING:
                y = random.randint(0, min(6, LED_COUNT - 1))
                heat[y] = min(255, heat[y] + random.randint(160, 255))

            for i in range(LED_COUNT):
                strip.set_pixel_color(i, heat_color(heat[i]))

            strip.show()
            time.sleep(0.03)
    except KeyboardInterrupt:
        strip.clear()
        strip.show()


if __name__ == "__main__":
    main()
