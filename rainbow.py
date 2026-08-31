import colorsys
import sys
import time
from rpi5_ws2812.ws2812 import Color
from led_common import LED_COUNT, get_strip

SPEED = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0


def wheel_color(position: float) -> Color:
    r, g, b = colorsys.hsv_to_rgb(position % 1.0, 1.0, 1.0)
    return Color(int(r * 255), int(g * 255), int(b * 255))


def main():
    strip = get_strip()
    try:
        offset = 0.0
        while True:
            for i in range(LED_COUNT):
                position = (i / LED_COUNT) + offset
                strip.set_pixel_color(i, wheel_color(position))
            strip.show()
            offset += 0.005 * SPEED
            time.sleep(0.02)
    except KeyboardInterrupt:
        strip.clear()
        strip.show()


if __name__ == "__main__":
    main()
