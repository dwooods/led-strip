# led-strip

A menu-driven controller for an addressable SK6812/WS2812B-compatible LED strip on a **Raspberry Pi 5**, driven over hardware SPI. Pick an animated effect from a terminal menu; it runs in the background until you swap to another one, turn the strip off, or quit.

**New here?** Read [JOURNEY.md](JOURNEY.md) for the full story of how this project got built — the Pi 5 GPIO gotcha, hardware wiring decisions, and what building all eleven effects taught along the way.

## Hardware

- Raspberry Pi 5
- Adafruit-style NeoPixel-compatible strip (SK6812 chips, WS2812B-protocol-compatible), 5V, 3-wire (GND / DIN / 5V)
- Strip **DIN** → Pi **GPIO10 / MOSI** (physical pin 19)
- Strip **GND** → shared ground with both the Pi and the strip's own external power supply
- Strip **5V** → an external power supply only — **never** the Pi's own 5V pin (a full strip at full brightness can pull several amps, well beyond what the Pi should source)
- A 300–500Ω resistor in series on DIN, and/or a 74AHCT125 logic-level shifter, improves reliability (Pi GPIO is 3.3V logic driving a nominally-5V strip) — a short run often works fine direct

The Pi 5 moved GPIO handling to a dedicated RP1 chip, which breaks the classic `rpi_ws281x` / Adafruit `neopixel` libraries (they rely on direct PWM+DMA register access). This project drives the strip over hardware SPI instead, via [`rpi5-ws2812`](https://pypi.org/project/rpi5-ws2812/), which sidesteps that problem entirely.

## Setup

```bash
# enable SPI
sudo raspi-config   # Interface Options -> SPI -> Enable, then reboot

git clone https://github.com/dwooods/led-strip.git
cd led-strip
python3 -m venv venv
source venv/bin/activate
pip install rpi5-ws2812   # needs Python 3.11+
```

`led_common.py` sets `LED_COUNT` (default 60) — update it to match your strip.

## Running it

```bash
./run.sh
```

`run.sh` creates the venv on first run only, activates it, and launches the menu. It's symlinked as `ledstrip` on `PATH` (`ln -s ~/led-strip/run.sh ~/.local/bin/ledstrip`), so once set up you can just type:

```bash
ledstrip
```

from anywhere. At the menu, typing a key runs that effect; typing a key followed by a number (e.g. `4 2`) passes that number through as the effect's optional speed/rate/intensity multiplier (default `1`).

## Preview effects in your browser

`simulator.html` reimplements every effect below in JavaScript and runs it on a virtual 60-pixel strip — no Pi, no wiring, no venv. Clone the repo and open `simulator.html` directly (double-click it, or drag it into a browser tab); it's a single self-contained file with no server or build step required.

Pick an effect from the dropdown and it starts animating immediately; changing the number field (speed/rate/BPM/intensity, matching that effect's optional argument above) restarts it with the new value, the same way picking a key with a number does on the real menu. It's a close port of each effect's actual logic, not just a lookalike — useful for previewing a pattern, or for testing a new one, without needing the hardware in front of you.

## Effects

| Key | Effect | Notes |
|---|---|---|
| 1 | Rainbow | Sliding rainbow; optional speed multiplier |
| 2 | Heartbeat | Traveling "lub-dub" pulse from center outward; optional BPM |
| 3 | Pac-Man chase | Pac-Man chasing 4 classic-colored ghosts, eating pellets and an occasional cherry |
| 4 | Fire | Fire2012-style flame simulation; optional intensity multiplier |
| 5 | Pong | Self-playing Pong between paddle zones at each end; optional speed multiplier |
| 6 | Fireworks | Rockets launch from pixel 0 and burst into fading colored particles; optional launch-rate multiplier |
| 7 | Explosions | Random blasts pop up anywhere on the strip with white-hot embers; optional rate multiplier |
| 8 | Rocket Launch | A rocket climbs from the pad against a twinkling starfield, trailing an accelerating flame; optional speed multiplier |
| 9 | Water Ripples | Ripples originate from the middle of the strip and expand symmetrically outward over a calm dark-blue base; optional rate multiplier |
| a | Twinkling Stars | A fixed invented constellation ("The Wayfarer") stays lit while background stars twinkle and occasional shooting stars streak past; optional shooting-star-rate multiplier |
| b | Plane Flyby | A single plane cruises end-to-end with nav lights, an anti-collision strobe, and a fading contrail, alternating direction each pass; optional speed multiplier |
| o | Turn off | Clears the strip and exits (not a looping effect — runs once, blocking) |
| q | Quit | Stops whatever's running and exits the menu |

## Architecture

- **`led_common.py`** — shared helpers only: `LED_COUNT` and `get_strip(brightness=0.5)`. Every effect imports from here instead of duplicating strip setup.
- **One file per effect** (`rainbow.py`, `fire.py`, `dogfight.py`, …) — each a standalone script with its own `if __name__ == "__main__":`, wrapping its animation loop in `try/except KeyboardInterrupt` that calls `strip.clear(); strip.show()` before exiting, so an interrupt always leaves the strip off rather than frozen mid-pattern. Optional numeric parameters are read from `sys.argv[1]` with a sensible default.
- **`led.py`** — the menu/launcher. `PROGRAMS` is a list of `(key, name, filename, hint)` tuples built into a `PROGRAM_MAP` dict, so each effect has an explicit, stable key rather than a position-derived number. Picking a key starts that effect as a background subprocess and immediately returns to the prompt; picking a new key (or `o`/`q`) first sends the currently running effect `SIGINT` and waits for it to exit, so only one effect ever drives the SPI bus at a time. `off.py` is the one exception — it's a one-shot action (not a looping animation), triggered by `o` as a special case before the `PROGRAM_MAP` lookup, and run synchronously so its confirmation message prints cleanly before the menu redraws.
- **`run.sh`** — creates the venv only if it doesn't already exist, activates it, and runs `led.py`.

## Adding a new effect

1. Create `newthing.py` following the pattern above (import from `led_common`, wrap the loop in `try/except KeyboardInterrupt`, add an optional `sys.argv` parameter if it makes sense).
2. Add one `(key, name, filename, hint)` tuple to `PROGRAMS` in `led.py`, using the next unused key in sequence (`1`–`9`, then `a`, `b`, `c`, … — never `o` or `q`, which are reserved).

Nothing else needs to change — `led.py`'s subprocess handling, key dispatch, and stop-before-switch logic are all generic.

To add it to `simulator.html` too, port the effect's `init`/`step` logic into JS (each effect there is an object with `init(state)` and `step(state, dt, now)` writing into a shared `pixels` array), then register it in that file's `EFFECTS`, `ORDER`, and `HINTS`.

## License

MIT — see [LICENSE](LICENSE).
