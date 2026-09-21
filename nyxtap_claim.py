"""
ZeinthHub Project - UI Wrapper
Tidak mengubah logic asli nyxtap.py
"""
import os
import sys
import time
import random
import shutil
import importlib.util

# ============================================================
#  ZEINTHUB PROJECT - THEME COLORS
# ============================================================
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
BLINK   = "\033[5m"

BLACK   = "\033[30m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"

BG_BLACK = "\033[40m"

NEON_GREEN = "\033[38;5;46m"
NEON_CYAN  = "\033[38;5;51m"
NEON_PINK  = "\033[38;5;201m"
NEON_PURPLE= "\033[38;5;99m"

W = "\033[0m"

# ============================================================
#  CLEAR & TERMINAL SIZE
# ============================================================
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def term_width():
    try:
        return shutil.get_terminal_size((80, 24)).columns
    except Exception:
        return 80

def center(text, width=None):
    w = width or term_width()
    # strip ANSI untuk hitung panjang visible
    import re
    clean = re.sub(r"\033\[[0-9;]*m", "", text)
    pad = max(0, (w - len(clean)) // 2)
    return " " * pad + text

# ============================================================
#  MATRIX RAIN EFFECT
# ============================================================
def matrix_rain(duration=2.5):
    chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノ"
    width = min(term_width(), 100)
    height = 12
    columns = [random.randint(0, height) for _ in range(width)]
    end_time = time.time() + duration
    try:
        while time.time() < end_time:
            lines = []
            for y in range(height):
                row = ""
                for x in range(width):
                    if columns[x] == y:
                        row += NEON_GREEN + random.choice(chars) + RESET
                    elif columns[x] - 1 == y or columns[x] - 2 == y:
                        row += GREEN + random.choice(chars) + RESET
                    else:
                        row += " "
                lines.append(row)
            sys.stdout.write("\033[H\033[J")
            sys.stdout.write("\n".join(lines))
            sys.stdout.flush()
            for i in range(width):
                if random.random() < 0.15:
                    columns[i] = 0
                else:
                    columns[i] += 1
                    if columns[i] > height + 4:
                        columns[i] = 0
            time.sleep(0.08)
    except KeyboardInterrupt:
        pass

# ============================================================
#  BANNER
# ============================================================
BANNER = r"""
   ███████╗███████╗██╗███╗   ██╗████████╗██╗  ██╗██╗  ██╗██╗   ██╗██████╗ 
   ╚══███╔╝██╔════╝██║████╗  ██║╚══██╔══╝██║  ██║██║  ██║██║   ██║██╔══██╗
     ███╔╝ █████╗  ██║██╔██╗ ██║   ██║   ███████║███████║██║   ██║██████╔╝
    ███╔╝  ██╔══╝  ██║██║╚██╗██║   ██║   ██╔══██║██╔══██║██║   ██║██╔══██╗
   ███████╗███████╗██║██║ ╚████║   ██║   ██║  ██║██║  ██║╚██████╔╝██████╔╝
   ╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ 
"""

TELEGRAM_LOGO = r"""
        ╭──────────────────────────────────╮
        │        ✈  TELEGRAM  ✈            │
        │                                  │
        │      t.me/Bleszh                 │
        ╰──────────────────────────────────╯
"""

def print_banner():
    clear()
    print()
    for line in BANNER.splitlines():
        print(center(NEON_CYAN + BOLD + line + RESET))
    print()
    print(center(NEON_GREEN + BOLD + "╔══════════════════════════════════════════════╗" + RESET))
    print(center(NEON_GREEN + BOLD + "║" + RESET + NEON_PINK + "   ZEINTHUB PROJECT  •  FAUCET AUTOMATION   " + RESET + NEON_GREEN + BOLD + "║" + RESET))
    print(center(NEON_GREEN + BOLD + "╚══════════════════════════════════════════════╝" + RESET))
    print()
    # Telegram box
    for line in TELEGRAM_LOGO.splitlines():
        print(center(NEON_CYAN + line + RESET))
    print()
    print(center(BLINK + NEON_PINK + BOLD + "⚡ SYSTEM GLITCHER ⚡" + RESET))
    print(center(DIM + WHITE + "powered by ZeinthHub" + RESET))
    print()

# ============================================================
#  LOADING SCREEN
# ============================================================
def loading_screen():
    clear()
    print()
    print(center(NEON_CYAN + BOLD + "▰▰▰ INITIALIZING ZEINTHUB CORE ▰▰▰" + RESET))
    print()
    steps = [
        ("Booting kernel modules", NEON_GREEN),
        ("Loading crypto libraries", NEON_CYAN),
        ("Spawning anti-bot bypass", NEON_PINK),
        ("Injecting stealth headers", NEON_PURPLE),
        ("Connecting to target host", NEON_GREEN),
        ("Calibrating emoji matcher", NEON_CYAN),
        ("Arming SYSTEM GLITCHER", NEON_PINK),
        ("Ready.", NEON_GREEN),
    ]
    spin = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    for i, (msg, color) in enumerate(steps):
        for _ in range(6):
            sys.stdout.write("\r" + center("%s  %s" % (spin[_ % len(spin)], color + msg + RESET)))
            sys.stdout.flush()
            time.sleep(0.05)
        # progress bar
        pct = int((i + 1) / len(steps) * 100)
        bar_len = 30
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write("\r" + center("%s  %s  [%s] %3d%%" % (
            color + "✔" + RESET, msg.ljust(28), NEON_GREEN + bar + RESET, pct)))
        sys.stdout.flush()
        time.sleep(0.12)
        print()
    print()
    print(center(NEON_GREEN + BOLD + "▰▰▰ SYSTEM READY ▰▰▰" + RESET))
    time.sleep(0.8)

# ============================================================
#  LOAD USER SCRIPT (nyxtap.py) TANPA MENGUBAHNYA
# ============================================================
def load_user_script(path):
    spec = importlib.util.spec_from_file_location("nyxtap_user", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# ============================================================
#  MAIN
# ============================================================
def main():
    # 1. Matrix rain dulu
    matrix_rain(duration=2.5)

    # 2. Banner
    print_banner()
    time.sleep(1.2)

    # 3. Loading screen
    loading_screen()

    # 4. Jalanin kode asli lo (TIDAK DIUBAH)
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nyxtap.py")
    if not os.path.exists(script_path):
        print("[!] nyxtap.py tidak ditemukan di folder yang sama.")
        sys.exit(1)

    print()
    print(center(NEON_CYAN + "─" * 50 + RESET))
    print(center(NEON_GREEN + BOLD + "  ▶  MENJALANKAN NYXTAP CLAIMER  ◀" + RESET))
    print(center(NEON_CYAN + "─" * 50 + RESET))
    print()

    user_mod = load_user_script(script_path)

    # Panggil main() asli dari kode lo
    try:
        user_mod.main()
    except KeyboardInterrupt:
        print("\n" + NEON_PINK + "[!] Dihentikan oleh user." + RESET)
    except SystemExit:
        pass

    # 5. Footer
    print()
    print(center(NEON_CYAN + "─" * 50 + RESET))
    print(center(NEON_GREEN + BOLD + "  ✈  Telegram : t.me/Bleszh" + RESET))
    print(center(NEON_PINK + BOLD + "  ⚡ ZeinthHub Project  •  SYSTEM GLITCHER" + RESET))
    print(center(NEON_CYAN + "─" * 50 + RESET))


if __name__ == "__main__":
    main()
