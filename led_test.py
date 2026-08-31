from rpi5_ws2812.ws2812 import Color, WS2812SpiDriver
import time

LED_COUNT = 60  # set to your strip's actual LED count

strip = WS2812SpiDriver(spi_bus=0, spi_device=0, led_count=LED_COUNT).get_strip()

strip.set_all_pixels(Color(255, 0, 0))  # red
strip.show()
time.sleep(2)

strip.set_all_pixels(Color(0, 0, 0))  # off
strip.show()
