import random
import time
from rpi5_ws2812.ws2812 import Color
from led_common import LED_COUNT, get_strip

PELLET_COLOR = Color(25, 25, 40)
OFF_COLOR = Color(0, 0, 0)
FLASH_COLOR = Color(255, 255, 255)
PACMAN_OPEN = Color(255, 255, 0)
PACMAN_CLOSED = Color(90, 70, 0)
CHERRY_COLOR = Color(220, 0, 60)
FRIGHTENED_COLOR = Color(150, 0, 220)
GHOST_COLORS = [
    Color(255, 0, 0),
    Color(255, 105, 180),
    Color(0, 255, 255),
    Color(255, 140, 0),
]

CHERRY_SPAWN_CHANCE = 0.006  # per-frame chance a cherry appears
FRIGHTENED_FRAMES = 65       # roughly 5 seconds at 0.08s/frame


def main():
    strip = get_strip()
    pellets = [True] * LED_COUNT
    pacman_pos = 0
    ghosts = [
        {"pos": (6 + i * 6) % LED_COUNT, "color": color}
        for i, color in enumerate(GHOST_COLORS)
    ]
    flash = None
    frame = 0
    cherry_pos = None
    frightened_frames = 0

    try:
        while True:
            frame += 1
            pacman_pos = (pacman_pos + 1) % LED_COUNT
            pellets[pacman_pos] = False

            for ghost in ghosts:
                if random.random() > 0.15:
                    ghost["pos"] = (ghost["pos"] + 1) % LED_COUNT
                if ghost["pos"] == pacman_pos:
                    flash = (ghost["pos"], 4)
                    ghost["pos"] = (pacman_pos + random.randint(15, 25)) % LED_COUNT

            if not any(pellets):
                pellets = [True] * LED_COUNT
                pellets[pacman_pos] = False

            if cherry_pos is None and frightened_frames <= 0 and random.random() < CHERRY_SPAWN_CHANCE:
                candidate = random.randrange(LED_COUNT)
                if candidate != pacman_pos:
                    cherry_pos = candidate

            if cherry_pos is not None and pacman_pos == cherry_pos:
                cherry_pos = None
                frightened_frames = FRIGHTENED_FRAMES

            for i in range(LED_COUNT):
                strip.set_pixel_color(i, PELLET_COLOR if pellets[i] else OFF_COLOR)

            if cherry_pos is not None:
                strip.set_pixel_color(cherry_pos, CHERRY_COLOR)

            for ghost in ghosts:
                color = FRIGHTENED_COLOR if frightened_frames > 0 else ghost["color"]
                strip.set_pixel_color(ghost["pos"], color)

            if flash and flash[1] > 0:
                strip.set_pixel_color(flash[0], FLASH_COLOR)
                flash = (flash[0], flash[1] - 1)

            chomp_open = (frame % 4) < 2
            strip.set_pixel_color(pacman_pos, PACMAN_OPEN if chomp_open else PACMAN_CLOSED)

            if frightened_frames > 0:
                frightened_frames -= 1

            strip.show()
            time.sleep(0.08)
    except KeyboardInterrupt:
        strip.clear()
        strip.show()


if __name__ == "__main__":
    main()
