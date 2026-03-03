import sys

import pygame

from player_registry import build_player, get_display_name, get_player_options, is_human_type
from ui import GameUI


PLAYER_OPTIONS = get_player_options()


def build_winner_text(status: str, player_types: dict[str, str]) -> str:
    if status == "Draw":
        return "Draw"

    if status in ("X wins", "O wins"):
        sign = status[0]
        selected_type = player_types.get(sign, "human")
        display_name = get_display_name(selected_type, sign)
        return f"{sign}: {display_name} wins"

    return status


def run():
    ui = GameUI()
    state = ui.state

    player_types = {
        "X": "human",
        "O": "random_ai",
    }

    players = {
        "X": build_player("X", player_types["X"]),
        "O": build_player("O", player_types["O"]),
    }

    screen_mode = "menu"
    open_dropdown = None
    menu_buttons = ui.draw_menu(player_types["X"], player_types["O"], PLAYER_OPTIONS, open_dropdown, pygame.mouse.get_pos())
    game_over_buttons = None
    escape_menu_buttons = None
    escape_return_mode = "playing"

    while True:
        current_player = players[state.turn] if screen_mode == "playing" else None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ui.close()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if screen_mode in ("playing", "game_over"):
                    escape_return_mode = screen_mode
                    screen_mode = "escape_menu"
                    game_over_buttons = None
                    escape_menu_buttons = ui.draw_escape_menu()
                elif screen_mode == "escape_menu":
                    screen_mode = escape_return_mode
                    escape_menu_buttons = None
                    if screen_mode == "game_over":
                        game_over_buttons = ui.draw_game_over(build_winner_text(state.status, player_types))
                    else:
                        ui.draw_game()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and screen_mode == "playing":
                state.reset()
                game_over_buttons = None
                ui.draw_game()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if screen_mode == "menu":
                    selected_option = False

                    if open_dropdown == "X":
                        for value, option_rect in menu_buttons["x_options"]:
                            if option_rect.collidepoint(mx, my):
                                player_types["X"] = value
                                open_dropdown = None
                                selected_option = True
                                break

                    if not selected_option and open_dropdown == "O":
                        for value, option_rect in menu_buttons["o_options"]:
                            if option_rect.collidepoint(mx, my):
                                player_types["O"] = value
                                open_dropdown = None
                                selected_option = True
                                break

                    if selected_option:
                        menu_buttons = ui.draw_menu(
                            player_types["X"],
                            player_types["O"],
                            PLAYER_OPTIONS,
                            open_dropdown,
                            pygame.mouse.get_pos(),
                        )
                    elif menu_buttons["x_dropdown"].collidepoint(mx, my):
                        open_dropdown = None if open_dropdown == "X" else "X"
                        menu_buttons = ui.draw_menu(
                            player_types["X"],
                            player_types["O"],
                            PLAYER_OPTIONS,
                            open_dropdown,
                            pygame.mouse.get_pos(),
                        )
                    elif menu_buttons["o_dropdown"].collidepoint(mx, my):
                        open_dropdown = None if open_dropdown == "O" else "O"
                        menu_buttons = ui.draw_menu(
                            player_types["X"],
                            player_types["O"],
                            PLAYER_OPTIONS,
                            open_dropdown,
                            pygame.mouse.get_pos(),
                        )
                    elif menu_buttons["start"].collidepoint(mx, my):
                        players = {
                            "X": build_player("X", player_types["X"]),
                            "O": build_player("O", player_types["O"]),
                        }
                        state.reset()
                        screen_mode = "playing"
                        open_dropdown = None
                        game_over_buttons = None
                        ui.draw_game()
                    else:
                        open_dropdown = None
                        menu_buttons = ui.draw_menu(
                            player_types["X"],
                            player_types["O"],
                            PLAYER_OPTIONS,
                            open_dropdown,
                            pygame.mouse.get_pos(),
                        )

                elif (
                    screen_mode == "playing"
                    and not state.game_over
                    and is_human_type(player_types[state.turn])
                ):
                    cell = ui.pixel_to_cell(mx, my)
                    if cell is not None and state.apply_move(cell[0], cell[1]):
                        ui.draw_game()
                        if state.game_over:
                            screen_mode = "game_over"
                            game_over_buttons = ui.draw_game_over(build_winner_text(state.status, player_types))

                elif screen_mode == "game_over" and game_over_buttons is not None:
                    if game_over_buttons["play_again"].collidepoint(mx, my):
                        state.reset()
                        players = {
                            "X": build_player("X", player_types["X"]),
                            "O": build_player("O", player_types["O"]),
                        }
                        screen_mode = "playing"
                        game_over_buttons = None
                        ui.draw_game()
                    elif game_over_buttons["main_menu"].collidepoint(mx, my):
                        state.reset()
                        screen_mode = "menu"
                        open_dropdown = None
                        game_over_buttons = None
                        menu_buttons = ui.draw_menu(
                            player_types["X"],
                            player_types["O"],
                            PLAYER_OPTIONS,
                            open_dropdown,
                            pygame.mouse.get_pos(),
                        )

                elif screen_mode == "escape_menu" and escape_menu_buttons is not None:
                    if escape_menu_buttons["resume"].collidepoint(mx, my):
                        screen_mode = escape_return_mode
                        escape_menu_buttons = None
                        if screen_mode == "game_over":
                            game_over_buttons = ui.draw_game_over(build_winner_text(state.status, player_types))
                        else:
                            ui.draw_game()
                    elif escape_menu_buttons["reset"].collidepoint(mx, my):
                        state.reset()
                        players = {
                            "X": build_player("X", player_types["X"]),
                            "O": build_player("O", player_types["O"]),
                        }
                        screen_mode = "playing"
                        escape_menu_buttons = None
                        ui.draw_game()
                    elif escape_menu_buttons["main_menu"].collidepoint(mx, my):
                        state.reset()
                        screen_mode = "menu"
                        open_dropdown = None
                        escape_menu_buttons = None
                        menu_buttons = ui.draw_menu(
                            player_types["X"],
                            player_types["O"],
                            PLAYER_OPTIONS,
                            open_dropdown,
                            pygame.mouse.get_pos(),
                        )

        if screen_mode == "menu":
            menu_buttons = ui.draw_menu(
                player_types["X"],
                player_types["O"],
                PLAYER_OPTIONS,
                open_dropdown,
                pygame.mouse.get_pos(),
            )

        if screen_mode == "playing" and not state.game_over and not is_human_type(player_types[state.turn]):
            ai_player = players[state.turn]
            move = ai_player.choose_move(state.snapshot(), state.legal_moves())
            if move is not None and state.apply_move(move[0], move[1]):
                ui.draw_game()
                if state.game_over:
                    screen_mode = "game_over"
                    game_over_buttons = ui.draw_game_over(build_winner_text(state.status, player_types))

        if screen_mode == "playing" and state.game_over and game_over_buttons is None:
            screen_mode = "game_over"
            game_over_buttons = ui.draw_game_over(build_winner_text(state.status, player_types))

        ui.tick()


if __name__ == "__main__":
    run()