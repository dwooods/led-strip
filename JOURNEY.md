# Building an LED Strip Controller on a Raspberry Pi 5: A Journey

*Repo: [github.com/dwooods/led-strip](https://github.com/dwooods/led-strip)*

This is the story of how a Raspberry Pi 5 and a strip of addressable LEDs turned into a menu-driven effects engine with eleven animated patterns, a browser-based simulator, and a public GitHub repo — and everything that had to be figured out along the way.

## The starting point

The goal was simple on paper: plug an addressable LED strip into a Raspberry Pi 5 and make it do interesting things — colors, animations, patterns that react and evolve rather than just sitting on one static color. The strip itself is an Adafruit-style NeoPixel-compatible strip using SK6812 chips (WS2812B-protocol-compatible), 5V, with three wires per cut point: GND, DIN, and 5V, all labeled directly on the flex PCB.

The first surprise came before a single LED lit up.

## The Pi 5 problem nobody warns you about

Almost every LED strip tutorial on the internet — and there are thousands — tells you to use `rpi_ws281x` or the Adafruit `neopixel` Python library. Both work great on a Raspberry Pi 4 or older. Neither works on a Raspberry Pi 5.

The reason is architectural: on every Pi before the 5, GPIO pins were controlled directly by the main SoC, and libraries like `rpi_ws281x` took advantage of that by talking straight to `/dev/mem` and driving the strip's precise timing requirements via PWM and DMA. The Pi 5 changed this. GPIO is now handled by a separate southbridge chip called **RP1**, sitting between the SoC and the pin header. That old direct-register trick simply doesn't reach the pins anymore — it doesn't error dramatically, it just doesn't work, or works unreliably, which is often more confusing than an outright failure.

This is the single biggest thing worth knowing before starting a Pi 5 GPIO project of any kind, and it isn't just an LED problem — it's the reason `RPi.GPIO` itself is unreliable on Pi 5, and why any tutorial that predates the Pi 5 needs a translation step.

The fix, once identified, was to stop trying to drive the strip through the general-purpose PWM/DMA path and instead go over **hardware SPI**. The [`rpi5-ws2812`](https://pypi.org/project/rpi5-ws2812/) PyPI package does exactly this — it treats the LED data line as an SPI data stream, which the RP1 chip handles natively and reliably. That one substitution — SPI instead of direct PWM/DMA — is what unlocked the entire rest of the project.

## The hardware, and the decisions behind it

The final wiring:

- **Strip DIN → Pi GPIO10 / MOSI** (physical pin 19) — this is the SPI data line the driver expects.
- **Strip GND → shared ground** with both the Pi and the strip's own external power supply. Every component needs a common ground reference or signal timing gets unpredictable.
- **Strip 5V → an external power supply only, never the Pi's own 5V pin.** This was a deliberate, non-negotiable design decision. A strip like this can draw several amps at full brightness/full white — far more current than the Pi's onboard 5V rail is meant to source. Trying to power the strip from the Pi risks brownouts, resets, or damage to the Pi itself.
- A 300–500Ω resistor in series on the data line, and/or a 74AHCT125 logic-level shifter, was noted as good practice, since the Pi's GPIO runs at 3.3V logic while the strip nominally expects 5V logic. In practice, for a short cable run, driving it direct from the 3.3V line worked fine — a good reminder that "best practice" and "what you strictly need for your specific run length" aren't always the same thing, and it's fine to try the simple thing first and add protection only if signal reliability becomes a problem.

One other lesson worth calling out: identifying the strip correctly mattered more than any generic "red is always X" wire-color assumption. The labels printed directly on the flex PCB at each cut point were the reliable source of truth for which wire was which — trusting silkscreen over convention avoided what could have been a wrong-wiring mistake early on.

## Software architecture: from one script to a system

The project didn't start as the multi-file structure it ended up as — it grew into it, one effect at a time, and the shape of `led.py` and friends today reflects real decisions made in response to real friction:

- **`led_common.py`** exists purely because every single effect needs the same two things: how many LEDs are on the strip (`LED_COUNT`, 60 in this setup) and a configured `Strip` object (`get_strip(brightness=0.5)`). Factoring that out once meant every new effect script could just import it instead of re-deriving strip setup each time — a small thing, but it's the difference between one place to change the LED count and eleven.
- **One Python file per effect**, each fully standalone with its own `if __name__ == "__main__":` block. This was a conscious choice over one giant script with a mode switch — it meant each effect could be developed, tested, and run completely independently (`python3 fire.py` just works on its own), and a bug in one effect can never take down another.
- **A universal cleanup pattern**: every effect wraps its animation loop in `try/except KeyboardInterrupt`, and on interrupt calls `strip.clear(); strip.show()` before exiting. Without this, killing an effect (e.g., to switch to another one) would leave the strip frozen mid-pattern — a stray red pixel glowing at 2am is a small bug, but an annoying one, and this pattern eliminates it everywhere at once rather than needing to be remembered per-effect.
- **An optional-parameter convention**: any effect that has a natural "speed," "rate," "BPM," or "intensity" knob reads it from `sys.argv[1]` with a sensible default (`SPEED = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0`). This one convention, applied consistently, is what let the menu support "type a key, optionally followed by a number" for *any* effect without the menu needing to know anything about what that number means.
- **`led.py`**, the menu/launcher, is the piece that ties it together — and the one that needed the most actual engineering. Two problems had to be solved:
  1. *Only one effect can safely drive the strip at a time* — two effects racing to write to the same SPI device would corrupt the display. The solution was to track whichever effect subprocess is currently running, and before launching a new one, send the old one `SIGINT` and wait for it to exit (triggering its own cleanup) before starting the next.
  2. *Picking an effect shouldn't block the menu.* Effects are meant to run indefinitely until swapped out, so `led.py` launches each one as a background subprocess and returns immediately to the prompt, rather than waiting on it.

  Keys are explicit and stable (`PROGRAMS` is a list of `(key, name, filename, hint)` tuples built into a `PROGRAM_MAP` dict) rather than derived from list position — so adding a new effect later never risks shifting what an existing key does. `1`–`9` filled up first; after that, letters continue (`a`, `b`, `c`, ...) rather than jumping to two-digit numbers, keeping every key a single keystroke.

  `off.py` is the one deliberate exception to "every effect is a backgrounded loop" — turning the strip off is a one-shot action, not an animation, so it's triggered by a special-cased `o` check before the `PROGRAM_MAP` lookup, and run synchronously (blocking) so its confirmation message prints cleanly instead of racing the menu's redraw.
- **`run.sh`**, symlinked as `ledstrip` on `PATH`, exists to erase the "wait, was it `source venv/bin/activate` first or `cd` first?" friction of getting the whole thing running. It creates the venv only if one doesn't already exist (so re-running it doesn't nuke a working environment) and launches the menu. The result: typing `ledstrip` from anywhere just works.

The net effect of all this structure is that **adding a new effect is now a two-step, low-risk operation**: write `newthing.py` following the established pattern, and add one tuple to `PROGRAMS`. Nothing else in `led.py` needs to know the new effect exists.

## Eleven effects, and what each one taught

Building eleven distinct animated patterns on the same 60-LED strip meant a lot of the same underlying techniques got reused, refined, and combined in new ways. A few threads run through all of them:

**The Fire2012 heat-color gradient** — a classic algorithm for mapping a "heat" value (0–255) to a fire-like red→orange→yellow→white color ramp — started life in `fire.py` as a straightforward flame simulation, but turned out to be reusable well beyond fire. `explosions.py` uses the same gradient for cooling ember particles flying outward from a blast center. `rocket.py` uses it again for an accelerating engine flame trailing a climbing rocket. Once the gradient function existed as a clean, tested piece of logic, it became the default choice any time an effect needed something to look "hot" — a good example of how a good utility function pays for itself multiple times over.

**Physical/particle simulation** shows up in several effects rather than just one style of flicker. `explosions.py` gives each ember an initial random velocity, applies drag over time, and lets particles die out once their heat is spent — a small physics simulation running per-frame on a 1D strip. `pong.py` and `fireworks.py` extend the same idea to trajectories and collisions. `dogfight.py` (built but not yet deployed to the physical strip — more on that below) pushed this furthest, with two planes closing distance, a tracer projectile, and a proximity-based fallback so a pass always resolves even if a shot doesn't land in time.

**Wave/ripple math** was the core problem in `water.py`: ripples originate from the center of the strip and expand symmetrically outward in both directions, each ring modeled as a Gaussian pulse (`math.exp(-((distance - radius) ** 2) / (2 * width ** 2))`) riding outward at a constant speed and fading exponentially over time. Multiple ripples overlapping just add their intensities together, which is what gives overlapping ripples a genuine "interference" look rather than one ripple simply overwriting another. Mixing two ripple "sizes" (a rarer ~30% chance of a slower, brighter, wider ripple versus the common faster/dimmer/narrower kind) added variety without adding much code.

**Not everything needed to be that mathematical.** `twinkle.py` invented a small piece of "lore" — a fixed 7-pixel constellation nicknamed "The Wayfarer," placed at deliberately irregular fractional positions along the strip so it wouldn't look like an obviously regular pattern, gently pulsing in warm gold and never fully dark, while background stars twinkle independently with varied color temperature and occasional shooting stars streak past. It's a reminder that not every effect needs to simulate real physics to feel alive — sometimes a hand-placed detail does more for the final look than another layer of math.

**Character and narrative** effects like `pacman.py` (Pac-Man chasing four classic ghost colors down the strip, eating pellets, with a cherry power-up that turns the ghosts vulnerable-purple for a few seconds) and `plane.py` (a plane with distinct nav lights, a periodic anti-collision strobe, and a fading contrail, flying the strip end-to-end and alternating direction each pass) showed that a 60-pixel strip is enough canvas to tell a small story, not just render an abstract pattern.

## The GitHub publishing journey

Once the effects existed, the next step was putting the project somewhere it could be shared, tracked, and eventually referenced from a blog post. This sounds like the easy part — it mostly was, but it had its own small lessons.

**Getting `git` set up on the Pi** required configuring identity first (`git config --global user.name` / `user.email`) before the first commit would even go through — a one-time "author identity unknown" error that's easy to fix but easy to forget on a machine you don't `git commit` from often.

**Authentication was the real speed bump.** GitHub stopped accepting plain account passwords for `git push` years ago, which meant the first push attempt just sat there prompting for a password that would then get rejected. The fix was generating a classic Personal Access Token scoped to just `repo` access (deliberately narrow — no reason to grant more than "can push to my own repos") and using that token in place of a password. Once `git config --global credential.helper store` was set up, the token got cached — though it's worth noting that setting the credential helper doesn't retroactively cache anything; it only starts caching *from that point forward*, so one more prompt after enabling it was expected, not a bug.

**A file went missing on the first commit.** `dogfight.py` was referenced by `led.py` but hadn't actually made it onto the Pi's filesystem yet, so the initial `git commit` — 19 files, not 20 — simply didn't include it. Rather than scrambling to recreate the file from memory, the pragmatic call was to remove the `dogfight` menu entry from `led.py` (and later, when it was spotted, from the README's effects table too) so the repo accurately reflected what was actually deployed and working, rather than describing a feature that didn't exist yet on the hardware. That's a small but real lesson in keeping documentation honest to what's actually running versus what's aspirational — `dogfight.py`'s logic exists and was built, but it only gets added back to the repo and the menu once it's genuinely deployed to the Pi.

**A sensitive-data audit before making the repo's history public.** Before considering the repo "shareable," it's worth checking not just the current file tree but the *entire git history* for anything that shouldn't be public — passwords, tokens, API keys, SSH details, Wi-Fi credentials, IP addresses, personal email addresses. The reliable way to do this is a fresh clone into a clean directory (so nothing local or uncommitted can hide a problem) followed by a broad `grep` across both the working tree and full `git log` output for those patterns. This project came back clean, but the process is the valuable part — a repo's public history is forever, even if a "bad" commit is later reverted, so checking once before the first push (and again before any future push that touches something sensitive) is worth the few minutes it takes.

## A browser simulator, almost as a side quest

Partway through, an interesting question came up: could the effects be previewed without the actual hardware in front of you? The answer became `simulator.html` — a single self-contained HTML/CSS/JS file that reimplements all eleven effects' actual logic (not just a lookalike animation) running against a virtual 60-pixel strip in a browser tab, no server or build step required.

The architecture mirrors the Python side almost one-to-one: each effect is a JS object exposing `init(state)` and `step(state, dt, now)`, writing colors into a shared `pixels` array, driven by a `requestAnimationFrame` loop. Parameters (speed, rate, BPM) are captured only at `init()` time and changing the number field triggers a full effect reset — deliberately mirroring how the real Pi menu works, where an argument is only read once, at launch, not live-adjusted mid-run.

The simulator wasn't bug-free on the first pass. Sixty fixed-12px circular "bulbs" with `space-between` justification overflowed the available panel width by a couple hundred pixels, producing an unwanted horizontal scrollbar — noticeable specifically once "Twinkling Stars" was open, which happened to be one of the effects rendered widest with its containing elements. The fix was switching from fixed pixel widths to flexbox sizing (`flex: 1 1 0` with `aspect-ratio: 1`), which makes each bulb always exactly fill its share of the available row width regardless of strip length or container size — a more robust approach than hand-tuning a pixel count that would only be correct for one particular window width anyway.

The simulator got folded into the same repo and documented in the README right alongside the Python setup instructions, and the convention going forward is that any new effect gets built twice: once as the real `.py` file for the Pi, and once ported into `simulator.html`'s effect registry — keeping the "preview without hardware" option honest and up to date.

## Where it stands, and what's next

As of now, the repo carries 19 tracked files — `led_common.py`, eleven effect scripts (rainbow, heartbeat, pacman, fire, pong, fireworks, explosions, rocket, water, twinkle, plane), `led.py`, `off.py`, `led_test.py` (a small smoke-test script), `run.sh`, `simulator.html`, plus `README.md`, `LICENSE` (MIT), and `.gitignore` — with a commit history that honestly reflects the project's real evolution, dogfight-file mishap and all.

The pieces still sitting on the shelf: `dogfight.py` — a fully-designed two-plane aerial combat effect with tracer fire, particle-burst detonation, and a guaranteed-resolution proximity fallback — waiting for its file to actually make it onto the Pi so it can rejoin the menu, the README, and the simulator together, the way every other effect already has.

What this project ended up teaching, more than any single wiring diagram or algorithm, is the value of a few small disciplines compounding: one shared helper instead of eleven copies of the same setup code, one cleanup pattern applied everywhere instead of remembered per-file, one convention for optional parameters instead of one-off argument parsing per effect, and one honest git history instead of a repo that claims more than the hardware actually does yet. None of those are individually dramatic — but together they're the difference between "a folder of Pi scripts" and a project someone else could actually clone, run, and extend.
