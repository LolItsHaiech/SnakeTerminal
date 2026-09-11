import curses
import math
import random
import sys

CHARPOOL = list("abcdefghijklmnopqrstuvwxyz0123456789-_/|><*~'\"")
CHARPOOL.append(" ")  # space is included, but rendered specially so it's visible

ENTER_CH = "\u23ce"  # submit tile
BACK_CH = "\u232b"  # backspace tile
SPACE_DISPLAY = "\u2423"  # space tile

DIRS = {
    curses.KEY_UP: (-1, 0), ord('w'): (-1, 0),
    curses.KEY_DOWN: (1, 0), ord('s'): (1, 0),
    curses.KEY_LEFT: (0, -1), ord('a'): (0, -1),
    curses.KEY_RIGHT: (0, 1), ord('d'): (0, 1),
}

INITIAL_SPEED_MS = 160
MIN_SPEED_MS = 70
SPEEDUP_EVERY = 4
SPEEDUP_STEP_MS = 8

INIT_SPAWN_MODE = 1
# 0: random spawn
# 1: ordered, in the center

TILE_DENSITY = 0.06

INIT_SPAWN_LINE_WIDTH = 12
INIT_SPAWN_LINE_SPACE = 3


def run(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1)
    curses.init_pair(4, curses.COLOR_WHITE, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)  # space tile

    max_y, max_x = stdscr.getmaxyx()
    status_rows = 2
    board_h = max_y - status_rows - 2
    board_w = max_x - 2
    if board_h < 8 or board_w < 20:
        raise RuntimeError("terminal too small for snake-typer (need >= 22x12)")

    sy, sx = board_h // 2, board_w // 4
    snake = [(sy, sx - i) for i in range(3)]
    direction = (0, 1)

    tiles = {}

    def random_empty_cell():
        while True:
            y = random.randint(0, board_h - 1)
            x = random.randint(0, board_w - 1)
            if (y, x) not in snake and (y, x) not in tiles:
                return y, x

    def spawn_tile(ch):
        y, x = random_empty_cell()
        tiles[(y, x)] = ch

    def initial_spawn_tile():
        match (INIT_SPAWN_MODE):
            case 0:
                for ch in CHARPOOL:
                    y, x = random_empty_cell()
                    tiles[(y, x)] = ch

            case 1:
                lines = math.ceil(len(CHARPOOL) / INIT_SPAWN_LINE_WIDTH)
                h = (lines - 1) * INIT_SPAWN_LINE_SPACE
                w = (INIT_SPAWN_LINE_WIDTH - 1) * INIT_SPAWN_LINE_SPACE

                s_h = (board_h - h) // 2
                s_w = (board_w - w) // 2

                i, j = 0, 0
                for ch in CHARPOOL:
                    x = s_w + (i * INIT_SPAWN_LINE_SPACE)
                    y = s_h + (j * INIT_SPAWN_LINE_SPACE)
                    tiles[(y, x)] = ch
                    i += 1
                    if i == INIT_SPAWN_LINE_WIDTH:
                        i = 0
                        j += 1

    initial_spawn_tile()
    tiles[random_empty_cell()] = ENTER_CH
    tiles[random_empty_cell()] = BACK_CH

    typed = []
    speed = INITIAL_SPEED_MS
    eaten = 0

    def draw():
        stdscr.erase()
        stdscr.border()
        for (y, x), ch in tiles.items():
            if ch == " ":
                display_ch = SPACE_DISPLAY
                color = curses.color_pair(5)
            elif ch in (ENTER_CH, BACK_CH):
                display_ch = ch
                color = curses.color_pair(3)
            else:
                display_ch = ch
                color = curses.color_pair(2)
            try:
                stdscr.addstr(y + 1, x + 1, display_ch, color | curses.A_BOLD)
            except curses.error:
                pass
        for i, (y, x) in enumerate(snake):
            ch = "O" if i == 0 else "o"
            try:
                stdscr.addstr(y + 1, x + 1, ch, curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                pass
        cmd_line = "".join(typed)
        status1 = f" cmd> {cmd_line}"[: max_x - 1]
        status2 = f"Score:{eaten}  [WASD/arrows move, q quits]"[: max_x - 1]
        try:
            stdscr.addstr(max_y - 2, 0, status1, curses.color_pair(4))
            stdscr.addstr(max_y - 1, 0, status2, curses.color_pair(4))
        except curses.error:
            pass
        stdscr.refresh()

    stdscr.timeout(speed)
    draw()

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            return None
        if key in DIRS:
            ny, nx = DIRS[key]
            if (ny, nx) != (-direction[0], -direction[1]):
                direction = (ny, nx)

        head_y, head_x = snake[0]
        new_head = (head_y + direction[0], head_x + direction[1])

        if not (0 <= new_head[0] < board_h and 0 <= new_head[1] < board_w):
            return "".join(typed)
        if new_head in snake:
            return "".join(typed)

        snake.insert(0, new_head)

        if new_head in tiles:
            ch = tiles.pop(new_head)
            if ch == ENTER_CH:
                return "".join(typed)
            elif ch == BACK_CH:
                if typed:
                    typed.pop()
                if len(snake) > 3:
                    snake.pop()
                spawn_tile(BACK_CH)
            else:
                typed.append(ch)
                eaten += 1
                spawn_tile(ch)
                if eaten % SPEEDUP_EVERY == 0 and speed > MIN_SPEED_MS:
                    speed -= SPEEDUP_STEP_MS
                    stdscr.timeout(speed)
        else:
            snake.pop()

        draw()


if len(sys.argv) < 2:
    print("usage: game.py OUTPUT_FILE", file=sys.stderr)
    sys.exit(1)
out_path = sys.argv[1]
result = None
try:
    result = curses.wrapper(run)
except KeyboardInterrupt:
    result = None
if result is not None:
    with open(out_path, "w") as f:
        f.write(result)
