#!/usr/bin/env python3
"""rk-monitor: tiny interactive terminal monitor. Arrow keys move the
row selection; q quits. Requires a real terminal."""

import sys

UP = "\x1b[A"
DOWN = "\x1b[B"
ROWS = ["cpu", "mem", "net", "disk"]


def handle(seq, pos, n_rows):
    """Return the new cursor position for one key sequence."""
    if seq == UP:
        return max(0, pos - 1)
    if seq == DOWN:
        return min(n_rows - 1, pos + 1)
    return pos


def draw(pos):
    sys.stdout.write("\x1b[2J\x1b[H")
    for i, row in enumerate(ROWS):
        marker = ">" if i == pos else " "
        sys.stdout.write(f"{marker} {row}\n")
    sys.stdout.flush()


def main():
    if not sys.stdin.isatty():
        print("rk-monitor: an interactive terminal (TTY) is required", file=sys.stderr)
        sys.exit(2)
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    pos = 0
    try:
        tty.setraw(fd)
        draw(pos)
        while True:
            ch = sys.stdin.read(1)
            if ch == "q":
                break
            if ch == "\x1b":
                ch += sys.stdin.read(2)
                pos = handle(ch, pos, len(ROWS))
                draw(pos)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    print(f"selected:{ROWS[pos]}")


if __name__ == "__main__":
    main()
