import pygame

from game import GRID, GameState


class GameUI:
    SIZE = 600
    CELL = SIZE // GRID
    MARK_W = 14
    FPS = 60
    STATUS_H = 40
    BOARD_TOP = STATUS_H
    BOARD_BOTTOM = STATUS_H + SIZE

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.SIZE, self.SIZE + self.STATUS_H))
        pygame.display.set_caption("Ultimate Tic Tac Toe (WIP)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        self.title_font = pygame.font.SysFont(None, 52)
        self.menu_font = pygame.font.SysFont(None, 32)
        self.state = GameState()

    def _draw_button(self, rect: pygame.Rect, text: str, selected: bool = False, hovered: bool = False):
        if selected:
            fill = (190, 220, 255)
            border = (50, 100, 170)
        elif hovered:
            fill = (220, 228, 240)
            border = (65, 65, 65)
        else:
            fill = (230, 230, 230)
            border = (80, 80, 80)
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, border, rect, width=2, border_radius=8)
        label = self.menu_font.render(text, True, (20, 20, 20))
        self.screen.blit(label, label.get_rect(center=rect.center))

    def _draw_dropdown(
        self,
        rect: pygame.Rect,
        selected_label: str,
        is_open: bool,
        is_hovered: bool,
        options: list[tuple[str, str]],
    ):
        if is_open:
            fill = (220, 235, 255)
            border = (50, 100, 170)
        elif is_hovered:
            fill = (222, 228, 238)
            border = (60, 60, 60)
        else:
            fill = (235, 235, 235)
            border = (80, 80, 80)
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, border, rect, width=2, border_radius=8)

        label = self.menu_font.render(selected_label, True, (20, 20, 20))
        self.screen.blit(label, (rect.x + 14, rect.y + (rect.height - label.get_height()) // 2))

        cx = rect.right - 18
        cy = rect.y + rect.height // 2
        if is_open:
            points = [(cx - 7, cy + 4), (cx + 7, cy + 4), (cx, cy - 4)]
        else:
            points = [(cx - 7, cy - 4), (cx + 7, cy - 4), (cx, cy + 4)]
        pygame.draw.polygon(self.screen, (40, 40, 40), points)

        option_rects = []
        if is_open:
            for index, (value, _) in enumerate(options):
                option_rect = pygame.Rect(rect.x, rect.y + rect.height + 6 + index * 42, rect.width, 36)
                option_rects.append((value, option_rect))

        return option_rects

    def _draw_dropdown_options(
        self,
        option_rects: list[tuple[str, pygame.Rect]],
        options: list[tuple[str, str]],
        selected_value: str,
        hovered_value: str | None,
    ):
        if not option_rects:
            return

        labels = dict(options)
        first_rect = option_rects[0][1]
        last_rect = option_rects[-1][1]
        panel = pygame.Rect(
            first_rect.x - 6,
            first_rect.y - 6,
            first_rect.width + 12,
            (last_rect.bottom - first_rect.y) + 12,
        )
        pygame.draw.rect(self.screen, (245, 245, 245), panel, border_radius=10)
        pygame.draw.rect(self.screen, (80, 80, 80), panel, width=2, border_radius=10)

        for value, option_rect in option_rects:
            self._draw_button(option_rect, labels[value], value == selected_value, hovered=value == hovered_value)

    def draw_menu(
        self,
        x_type: str,
        o_type: str,
        options: list[tuple[str, str]],
        open_dropdown: str | None,
        hover_pos: tuple[int, int] | None = None,
    ):
        self.screen.fill((245, 245, 245))

        title = self.title_font.render("Ofurmylla", True, (20, 20, 20))
        self.screen.blit(title, title.get_rect(center=(self.SIZE // 2, 90)))

        x_label = self.menu_font.render("X Player", True, (20, 20, 20))
        self.screen.blit(x_label, (110, 180))
        o_label = self.menu_font.render("O Player", True, (20, 20, 20))
        self.screen.blit(o_label, (110, 300))

        labels = dict(options)
        x_dropdown_rect = pygame.Rect(250, 170, 260, 44)
        o_dropdown_rect = pygame.Rect(250, 290, 260, 44)
        start_rect = pygame.Rect(220, 420, 160, 56)

        x_dropdown_hovered = hover_pos is not None and x_dropdown_rect.collidepoint(hover_pos)
        o_dropdown_hovered = hover_pos is not None and o_dropdown_rect.collidepoint(hover_pos)
        start_hovered = hover_pos is not None and start_rect.collidepoint(hover_pos)

        x_option_rects = self._draw_dropdown(
            x_dropdown_rect,
            labels[x_type],
            open_dropdown == "X",
            x_dropdown_hovered,
            options,
        )
        o_option_rects = self._draw_dropdown(
            o_dropdown_rect,
            labels[o_type],
            open_dropdown == "O",
            o_dropdown_hovered,
            options,
        )

        x_hovered_value = None
        for value, option_rect in x_option_rects:
            if hover_pos is not None and option_rect.collidepoint(hover_pos):
                x_hovered_value = value
                break

        o_hovered_value = None
        for value, option_rect in o_option_rects:
            if hover_pos is not None and option_rect.collidepoint(hover_pos):
                o_hovered_value = value
                break

        self._draw_button(start_rect, "Start Game", False, start_hovered)

        self._draw_dropdown_options(x_option_rects, options, x_type, x_hovered_value)
        self._draw_dropdown_options(o_option_rects, options, o_type, o_hovered_value)

        pygame.display.flip()

        return {
            "x_dropdown": x_dropdown_rect,
            "o_dropdown": o_dropdown_rect,
            "x_options": x_option_rects,
            "o_options": o_option_rects,
            "start": start_rect,
        }

    def draw_grid(self):
        pygame.draw.rect(self.screen, (245, 245, 245), (0, self.BOARD_TOP, self.SIZE, self.SIZE))

        for i in range(1, GRID):
            y = self.BOARD_TOP + i * self.CELL
            x = i * self.CELL
            pygame.draw.line(self.screen, (30, 30, 30), (x, self.BOARD_TOP), (x, self.BOARD_BOTTOM), 4)
            pygame.draw.line(self.screen, (30, 30, 30), (0, y), (self.SIZE, y), 4)

        for i in range(3, GRID, 3):
            y = self.BOARD_TOP + i * self.CELL
            x = i * self.CELL
            pygame.draw.line(self.screen, (200, 0, 0), (x, self.BOARD_TOP), (x, self.BOARD_BOTTOM), 10)
            pygame.draw.line(self.screen, (200, 0, 0), (0, y), (self.SIZE, y), 10)

    def draw_marks(self):
        pad = self.CELL * 0.18
        for r in range(GRID):
            for c in range(GRID):
                x0, y0 = c * self.CELL, r * self.CELL + self.STATUS_H
                if self.state.board[r][c] == "X":
                    pygame.draw.line(
                        self.screen,
                        (20, 20, 20),
                        (x0 + pad, y0 + pad),
                        (x0 + self.CELL - pad, y0 + self.CELL - pad),
                        self.MARK_W,
                    )
                    pygame.draw.line(
                        self.screen,
                        (20, 20, 20),
                        (x0 + self.CELL - pad, y0 + pad),
                        (x0 + pad, y0 + self.CELL - pad),
                        self.MARK_W,
                    )
                elif self.state.board[r][c] == "O":
                    pygame.draw.circle(
                        self.screen,
                        (20, 20, 20),
                        (x0 + self.CELL // 2, y0 + self.CELL // 2),
                        int(self.CELL * 0.32),
                        self.MARK_W,
                    )

    def draw_big_marks(self):
        pad = self.CELL * 0.35
        for sb_r in range(3):
            for sb_c in range(3):
                winner = self.state.big_board[sb_r][sb_c]
                if not winner:
                    continue

                x0 = sb_c * (self.CELL * 3)
                y0 = self.BOARD_TOP + sb_r * (self.CELL * 3)
                wsize = self.CELL * 3

                if winner == "X":
                    pygame.draw.line(
                        self.screen,
                        (10, 10, 10),
                        (x0 + pad, y0 + pad),
                        (x0 + wsize - pad, y0 + wsize - pad),
                        18,
                    )
                    pygame.draw.line(
                        self.screen,
                        (10, 10, 10),
                        (x0 + wsize - pad, y0 + pad),
                        (x0 + pad, y0 + wsize - pad),
                        18,
                    )
                elif winner == "O":
                    pygame.draw.circle(
                        self.screen,
                        (10, 10, 10),
                        (x0 + wsize // 2, y0 + wsize // 2),
                        int(wsize * 0.34),
                        18,
                    )

    def draw_allowed_highlight(self):
        overlay = pygame.Surface((self.SIZE, self.SIZE + self.STATUS_H), pygame.SRCALPHA)
        for sb_r, sb_c in self.state.allowed_subboards():
            x = sb_c * (self.CELL * 3)
            y = self.BOARD_TOP + sb_r * (self.CELL * 3)
            pygame.draw.rect(overlay, (255, 255, 0, 45), (x, y, self.CELL * 3, self.CELL * 3))
        self.screen.blit(overlay, (0, 0))

    def draw_status(self):
        status_surface = pygame.Surface((self.SIZE, self.STATUS_H))
        status_surface.fill((220, 220, 220))
        self.screen.blit(status_surface, (0, 0))
        text = self.state.status if self.state.game_over else f"Turn: {self.state.turn}   (Press R to reset)"
        label = self.font.render(text, True, (10, 10, 10))
        self.screen.blit(label, (10, 10))

    def draw_game(self):
        self.draw_grid()
        self.draw_allowed_highlight()
        self.draw_marks()
        self.draw_big_marks()
        self.draw_status()
        pygame.display.flip()

    def _draw_two_button_overlay(
        self,
        title_text: str,
        left_button_text: str,
        right_button_text: str,
        left_key: str,
        right_key: str,
    ):
        self.draw_game()

        overlay = pygame.Surface((self.SIZE, self.SIZE + self.STATUS_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(100, 180, 400, 240)
        pygame.draw.rect(self.screen, (245, 245, 245), panel, border_radius=12)
        pygame.draw.rect(self.screen, (80, 80, 80), panel, width=2, border_radius=12)

        title = self.menu_font.render(title_text, True, (20, 20, 20))
        self.screen.blit(title, title.get_rect(center=(self.SIZE // 2, 235)))

        left_rect = pygame.Rect(150, 300, 140, 52)
        right_rect = pygame.Rect(310, 300, 140, 52)

        self._draw_button(left_rect, left_button_text, False)
        self._draw_button(right_rect, right_button_text, False)

        pygame.display.flip()

        return {
            left_key: left_rect,
            right_key: right_rect,
        }

    def draw_game_over(self, result_text: str | None = None):
        winner_text = result_text if result_text else (self.state.status if self.state.status else "Game Over")
        return self._draw_two_button_overlay(
            winner_text,
            "Play Again",
            "Main Menu",
            "play_again",
            "main_menu",
        )

    def draw_escape_menu(self):
        self.draw_game()

        overlay = pygame.Surface((self.SIZE, self.SIZE + self.STATUS_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(100, 170, 400, 270)
        pygame.draw.rect(self.screen, (245, 245, 245), panel, border_radius=12)
        pygame.draw.rect(self.screen, (80, 80, 80), panel, width=2, border_radius=12)

        title = self.menu_font.render("Pause", True, (20, 20, 20))
        self.screen.blit(title, title.get_rect(center=(self.SIZE // 2, 225)))

        resume_rect = pygame.Rect(150, 270, 300, 46)
        reset_rect = pygame.Rect(150, 326, 145, 46)
        menu_rect = pygame.Rect(305, 326, 145, 46)

        self._draw_button(resume_rect, "Resume", False)
        self._draw_button(reset_rect, "Reset", False)
        self._draw_button(menu_rect, "Main Menu", False)

        pygame.display.flip()

        return {
            "resume": resume_rect,
            "reset": reset_rect,
            "main_menu": menu_rect,
        }

    def pixel_to_cell(self, mx: int, my: int):
        if my < self.STATUS_H:
            return None
        r = (my - self.STATUS_H) // self.CELL
        c = mx // self.CELL
        if not (0 <= r < GRID and 0 <= c < GRID):
            return None
        return r, c

    def tick(self):
        self.clock.tick(self.FPS)

    def close(self):
        pygame.quit()