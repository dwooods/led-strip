from led_common import get_strip


def main():
    strip = get_strip()
    strip.clear()
    strip.show()
    print("Strip turned off.")


if __name__ == "__main__":
    main()
