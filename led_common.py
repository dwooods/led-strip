from rpi5_ws2812.ws2812 import WS2812SpiDriver

LED_COUNT = 60  # set to your strip's actual LED count


def get_strip(brightness: float = 0.5):
    strip = WS2812SpiDriver(spi_bus=0, spi_device=0, led_count=LED_COUNT).get_strip()
    strip.set_brightness(brightness)
    return strip
