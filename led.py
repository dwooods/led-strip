import os
import signal
import subprocess
import sys

# Each entry: (key, name, filename, hint). Keys 1-9 are already used;
# once a menu fills up, use letters (a, b, c, ...) for new entries instead
# of jumping to two-digit numbers like 10. Skip "o" and "q" -- those are
# reserved for Turn Off and Quit below and are handled separately.
PROGRAMS = [
    ("1", "Rainbow", "rainbow.py", "default speed 1, or enter a number e.g. '1 3' for faster"),
    ("2", "Heartbeat", "heartbeat.py", "default 100, or enter a number e.g. '2 75'"),
    ("3", "Pac-Man chase", "pacman.py", ""),
    ("4", "Fire", "fire.py", "default intensity 1, or enter a number e.g. '4 2' for a wilder flame"),
    ("5", "Pong", "pong.py", "default speed 1, or enter a number e.g. '5 2' for faster rallies"),
    ("6", "Fireworks", "fireworks.py", "default rate 1, or enter a number e.g. '6 2' for more frequent bursts"),
    ("7", "Explosions", "explosions.py", "default rate 1, or enter a number e.g. '7 2' for more frequent blasts"),
    ("8", "Rocket Launch", "rocket.py", "default speed 1, or enter a number e.g. '8 2' for a faster climb"),
    ("9", "Water Ripples", "water.py", "default rate 1, or enter a number e.g. '9 2' for busier ripples"),
    ("a", "Twinkling Stars", "twinkle.py", "default rate 1, or enter a number e.g. 'a 2' for more frequent shooting stars"),
    ("b", "Plane Flyby", "plane.py", "default speed 1, or enter a number e.g. 'b 2' for a faster flyby"),
]

PROGRAM_MAP = {key: (name, filename, hint) for key, name, filename, hint in PROGRAMS}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def show_menu(running_name):
    print("\nLED Strip Control")
    for key, name, _, hint in PROGRAMS:
        line = f"  {key}. {name}"
        if hint:
            line += f"  ({hint})"
        print(line)
    print("  o. Turn off")
    print("  q. Quit")
    if running_name:
        print(f"\n  (currently running: {running_name} — pick another option to switch, or o/q to stop)")

def stop_process(proc):
    if proc is not None and proc.poll() is None:
        proc.send_signal(signal.SIGINT)
        proc.wait()

def main():
    current_proc = None
    current_name = None

    try:
        while True:
            show_menu(current_name)
            raw = input("\nSelect an option: ").strip()

            if raw.lower() == "q":
                stop_process(current_proc)
                break

            parts = raw.split()
            if not parts:
                continue

            choice, extra_args = parts[0], parts[1:]
            key = choice.lower()

            if key == "o":
                stop_process(current_proc)
                off_path = os.path.join(SCRIPT_DIR, "off.py")
                subprocess.run([sys.executable, off_path, *extra_args], cwd=SCRIPT_DIR)
                current_proc = None
                current_name = None
                continue

            if key not in PROGRAM_MAP:
                print("Invalid choice, try again.")
                continue

            stop_process(current_proc)

            name, filename, _ = PROGRAM_MAP[key]
            path = os.path.join(SCRIPT_DIR, filename)

            print(f"\nStarting {name} in the background...")
            current_proc = subprocess.Popen([sys.executable, path, *extra_args], cwd=SCRIPT_DIR)
            current_name = name
    except KeyboardInterrupt:
        stop_process(current_proc)
        print("\nQuitting.")

if __name__ == "__main__":
    main()
