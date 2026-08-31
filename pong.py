import random
import sys
import time
from rpi5_ws2812.ws2812 import Color
from led_common import LED_COUNT, get_strip

SPEED = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0

PADDLE_SIZE = 3
LEFT_COLOR = Color(0, 180, 255)
RIGHT_COLOR = Color(255, 120, 0)
LEFT_FLASH = Color(120, 220, 255)
RIGHT_FLASH = Color(255, 190, 120)
BALL_COLOR = Color(255, 255, 255)
TRAIL_COLOR = Color(60, 60, 60)
OFF_COLOR = Color(0, 0, 0)
SCORE_FLASH_FRAMES = 20
MISS_CHANCE = 0.08


def main():
    strip = get_strip()

    ball_pos = LED_COUNT / 2.0
    direction = random.choice([-1, 1])
    base_speed = 12.0 * SPEED
    speed = base_speed

    left_flash_frames = 0
    right_flash_frames = 0
    score_flash = None
    trail = []

    last_time = time.monotonic()

    try:
        while True:
            now = time.monotonic()
            dt = now - last_time
            last_time = now

            if score_flash is None:
                ball_pos += direction * speed * dt
                trail.append(ball_pos)
                trail = trail[-4:]

                left_edge = PADDLE_SIZE
                right_edge = LED_COUNT - 1 - PADDLE_SIZE

                if ball_pos <= left_edge and direction < 0:
                    if random.random() < MISS_CHANCE:
                        score_flash = ("right", SCORE_FLASH_FRAMES)
                    else:
                        direction = 1
                        speed += 1.5 * SPEED
                        left_flash_frames = 4
                        ball_pos = left_edge
                elif ball_pos >= right_edge and direction > 0:
                    if random.random() < MISS_CHANCE:
                        score_flash = ("left", SCORE_FLASH_FRAMES)
                    else:
                        direction = -1
                        speed += 1.5 * SPEED
                        right_flash_frames = 4
                        ball_pos = right_edge

            for i in range(LED_COUNT):
                strip.set_pixel_color(i, OFF_COLOR)

            for i in range(PADDLE_SIZE):
                strip.set_pixel_color(i, LEFT_FLASH if left_flash_frames > 0 else LEFT_COLOR)
            for i in range(LED_COUNT - PADDLE_SIZE, LED_COUNT):
                strip.set_pixel_color(i, RIGHT_FLASH if right_flash_frames > 0 else RIGHT_COLOR)

            if score_flash is None:
                for t_pos in trail[:-1]:
                    idx = int(round(t_pos))
                    if 0 <= idx < LED_COUNT:
                        strip.set_pixel_color(idx, TRAIL_COLOR)
                idx = int(round(ball_pos))
                if 0 <= idx < LED_COUNT:
                    strip.set_pixel_color(idx, BALL_COLOR)
            else:
                side, frames_left = score_flash
                flash_color = RIGHT_FLASH if side == "right" else LEFT_FLASH
                if frames_left % 2 == 0:
                    for i in range(LED_COUNT):
                        strip.set_pixel_color(i, flash_color)
                score_flash = (side, frames_left - 1)
                if score_flash[1] <= 0:
                    score_flash = None
                    ball_pos = LED_COUNT / 2.0
                    direction = random.choice([-1, 1])
                    speed = base_speed
                    trail = []

            if left_flash_frames > 0:
                left_flash_frames -= 1
            if right_flash_frames > 0:
                right_flash_frames -= 1

            strip.show()
            time.sleep(0.02)
    except KeyboardInterrupt:
        strip.clear()
        strip.show()


if __name__ == "__main__":
    main()
