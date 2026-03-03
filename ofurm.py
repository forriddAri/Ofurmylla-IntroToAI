import pygame
import sys

# --- Config ---
SIZE = 600
GRID = 9
CELL = SIZE // GRID
MARK_W = 14
FPS = 60
STATUS_H = 40

BOARD_TOP = STATUS_H
BOARD_BOTTOM = STATUS_H + SIZE

pygame.init()
screen = pygame.display.set_mode((SIZE, SIZE + STATUS_H))
pygame.display.set_caption("Ultimate Tic Tac Toe (WIP)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

def new_game():
    return [["" for _ in range(GRID)] for _ in range(GRID)], "X", False, ""

board, turn, game_over, status = new_game()
last_move = None  # stores (r, c) of last played cell
big_board = [[None for _ in range(3)] for _ in range(3)]  # winner of each 3x3 subboard: "X"/"O"/None

def draw_grid():
    # fill only board area
    pygame.draw.rect(screen, (245, 245, 245), (0, BOARD_TOP, SIZE, SIZE))

    # thin black lines
    for i in range(1, GRID):
        y = BOARD_TOP + i * CELL
        x = i * CELL
        pygame.draw.line(screen, (30, 30, 30), (x, BOARD_TOP), (x, BOARD_BOTTOM), 4)
        pygame.draw.line(screen, (30, 30, 30), (0, y), (SIZE, y), 4)

    # thicker red separators every 3
    for i in range(3, GRID, 3):
        y = BOARD_TOP + i * CELL
        x = i * CELL
        pygame.draw.line(screen, (200, 0, 0), (x, BOARD_TOP), (x, BOARD_BOTTOM), 10)
        pygame.draw.line(screen, (200, 0, 0), (0, y), (SIZE, y), 10)

def draw_marks():
    pad = CELL * 0.18
    for r in range(GRID):
        for c in range(GRID):
            x0, y0 = c * CELL, r * CELL + STATUS_H
            if board[r][c] == "X":
                pygame.draw.line(screen, (20, 20, 20),
                                 (x0 + pad, y0 + pad), (x0 + CELL - pad, y0 + CELL - pad), MARK_W)
                pygame.draw.line(screen, (20, 20, 20),
                                 (x0 + CELL - pad, y0 + pad), (x0 + pad, y0 + CELL - pad), MARK_W)
            elif board[r][c] == "O":
                pygame.draw.circle(screen, (20, 20, 20),
                                   (x0 + CELL // 2, y0 + CELL // 2), int(CELL * 0.32), MARK_W)

def draw_big_marks():
    # draw big X/O over won 3x3 subboards
    pad = CELL * 0.35
    for sb_r in range(3):
        for sb_c in range(3):
            w = big_board[sb_r][sb_c]
            if not w:
                continue

            x0 = sb_c * (CELL * 3)
            y0 = BOARD_TOP + sb_r * (CELL * 3)
            wsize = CELL * 3

            if w == "X":
                pygame.draw.line(screen, (10, 10, 10),
                                 (x0 + pad, y0 + pad),
                                 (x0 + wsize - pad, y0 + wsize - pad), 18)
                pygame.draw.line(screen, (10, 10, 10),
                                 (x0 + wsize - pad, y0 + pad),
                                 (x0 + pad, y0 + wsize - pad), 18)
            elif w == "O":
                pygame.draw.circle(screen, (10, 10, 10),
                                   (x0 + wsize // 2, y0 + wsize // 2),
                                   int(wsize * 0.34), 18)

def subboard_full(sb_r, sb_c):
    r0, c0 = sb_r * 3, sb_c * 3
    for rr in range(r0, r0 + 3):
        for cc in range(c0, c0 + 3):
            if board[rr][cc] == "":
                return False
    return True

def allowed_subboards():
    # already won subboards are not playable
    playable = [(sr, sc) for sr in range(3) for sc in range(3)
                if big_board[sr][sc] is None and not subboard_full(sr, sc)]

    if last_move is None:
        return playable

    r, c = last_move
    target = (r % 3, c % 3)

    # if target is playable, forced there
    if target in playable:
        return [target]

    # else anywhere playable
    return playable

def draw_allowed_highlight():
    overlay = pygame.Surface((SIZE, SIZE + STATUS_H), pygame.SRCALPHA)
    for sb_r, sb_c in allowed_subboards():
        x = sb_c * (CELL * 3)
        y = BOARD_TOP + sb_r * (CELL * 3)
        pygame.draw.rect(overlay, (255, 255, 0, 45), (x, y, CELL * 3, CELL * 3))
    screen.blit(overlay, (0, 0))

def check_subboard_win(sb_r, sb_c):
    r0, c0 = sb_r * 3, sb_c * 3

    # rows
    for r in range(3):
        row = [board[r0 + r][c0 + c] for c in range(3)]
        if row[0] and row.count(row[0]) == 3:
            return row[0]

    # cols
    for c in range(3):
        col = [board[r0 + r][c0 + c] for r in range(3)]
        if col[0] and col.count(col[0]) == 3:
            return col[0]

    d1 = [board[r0 + i][c0 + i] for i in range(3)]
    d2 = [board[r0 + i][c0 + 2 - i] for i in range(3)]

    if d1[0] and d1.count(d1[0]) == 3:
        return d1[0]
    if d2[0] and d2.count(d2[0]) == 3:
        return d2[0]

    return None

def check_bigboard_win():
    # rows
    for r in range(3):
        if big_board[r][0] and all(big_board[r][c] == big_board[r][0] for c in range(3)):
            return big_board[r][0]
    # cols
    for c in range(3):
        if big_board[0][c] and all(big_board[r][c] == big_board[0][c] for r in range(3)):
            return big_board[0][c]
    # diagonals
    if big_board[0][0] and all(big_board[i][i] == big_board[0][0] for i in range(3)):
        return big_board[0][0]
    if big_board[0][2] and all(big_board[i][2 - i] == big_board[0][2] for i in range(3)):
        return big_board[0][2]

    # draw if no playable subboards left
    if not allowed_subboards():
        return "DRAW"

    return None

def draw_status(text):
    s = pygame.Surface((SIZE, STATUS_H))
    s.fill((220, 220, 220))
    screen.blit(s, (0, 0))
    label = font.render(text, True, (10, 10, 10))
    screen.blit(label, (10, 10))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                board, turn, game_over, status = new_game()
                last_move = None
                big_board = [[None for _ in range(3)] for _ in range(3)]

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not game_over:
            mx, my = event.pos
            if my < STATUS_H:
                continue

            r = (my - STATUS_H) // CELL
            c = mx // CELL
            if not (0 <= r < GRID and 0 <= c < GRID):
                continue

            sb_r, sb_c = r // 3, c // 3
            if (sb_r, sb_c) not in allowed_subboards():
                continue

            if big_board[sb_r][sb_c] is not None:
                continue  # subboard already won

            if board[r][c] == "":
                board[r][c] = turn
                last_move = (r, c)

                # if that subboard now has a winner, mark it
                w = check_subboard_win(sb_r, sb_c)
                if w:
                    big_board[sb_r][sb_c] = w

                # check big board win
                bw = check_bigboard_win()
                if bw == "DRAW":
                    game_over = True
                    status = "Draw! (Press R)"
                elif bw in ("X", "O"):
                    game_over = True
                    status = f"{bw} wins! (Press R)"
                else:
                    turn = "O" if turn == "X" else "X"

    draw_grid()
    draw_allowed_highlight()
    draw_marks()
    draw_big_marks()
    draw_status(status if game_over else f"Turn: {turn}   (Press R to reset)")

    pygame.display.flip()
    clock.tick(FPS)