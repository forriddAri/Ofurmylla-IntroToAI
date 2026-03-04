import sys
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

import pygame

from player_registry import build_player, get_display_name, get_player_options, is_human_type
from ui import GameUI


PLAYER_OPTIONS = get_player_options()


def _compute_ai_move(ai_player: Any, state_snapshot: Any):
    has_game_attr = hasattr(ai_player, "game")
    original_game = getattr(ai_player, "game", None)

    if has_game_attr:
        setattr(ai_player, "game", state_snapshot)

    try:
        return ai_player.choose_move()
    finally:
        if has_game_attr:
            setattr(ai_player, "game", original_game)


def build_winner_text(status: str, player_types: dict[str, str]) -> str:
    if status == "Draw":
        return "Draw"

    if status in ("X wins", "O wins"):
        sign = status[0]
        selected_type = player_types.get(sign, "human")
        display_name = get_display_name(selected_type, sign)
        return f"{sign}: {display_name} wins"

    return status


def build_series_summary(player_types: dict[str, str], series_scores: dict[str, int]) -> tuple[str, list[str]]:
    x_type = player_types.get("X", "human")
    o_type = player_types.get("O", "human")

    x_role = "Human" if is_human_type(x_type) else get_display_name(x_type, "X")
    o_role = "Human" if is_human_type(o_type) else get_display_name(o_type, "O")

    if series_scores["X"] > series_scores["O"]:
        winner_text = "Player 1 wins"
    elif series_scores["O"] > series_scores["X"]:
        winner_text = "Player 2 wins"
    else:
        winner_text = "Series Draw"

    lines = [
        f"Player 1: {x_role}",
        f"Rounds won: {series_scores['X']}",
        f"Player 2: {o_role}",
        f"Rounds won: {series_scores['O']}",
        f"Draws: {series_scores['Draw']}",
    ]
    return winner_text, lines


def run():
    ui = GameUI()
    state = ui.state

    player_types = {
        "X": "human",
        "O": "random_ai",
    }

    players = {
        "X": build_player("X", player_types["X"], state),
        "O": build_player("O", player_types["O"], state),
    }

    screen_mode = "menu"
    open_dropdown = None
    rounds_input_text = "50"
    rounds_input_active = False
    menu_buttons = None
    game_over_buttons = None
    escape_menu_buttons = None
    escape_return_mode = "playing"

    series_total_rounds = 1
    series_current_round = 1
    series_scores = {
        "X": 0,
        "O": 0,
        "Draw": 0,
    }
    series_active = False
    match_has_human = True
    fast_simulation_enabled = True

    ai_executor = ThreadPoolExecutor(max_workers=2)
    ai_future: Future | None = None
    ai_expected_revision: int | None = None
    ai_expected_turn: str | None = None
    ai_expected_type: str | None = None
    state_revision = 0

    def bump_state_revision():
        nonlocal state_revision
        state_revision += 1

    def reset_state():
        state.reset()
        bump_state_revision()

    def apply_move_and_track(r: int, c: int) -> bool:
        if state.apply_move(r, c):
            bump_state_revision()
            return True
        return False

    def queue_ai_move_if_needed():
        nonlocal ai_future, ai_expected_revision, ai_expected_turn, ai_expected_type

        if ai_future is not None:
            return

        if screen_mode != "playing" or state.game_over:
            return

        current_turn = state.turn
        current_type = player_types[current_turn]
        if is_human_type(current_type):
            return

        state_snapshot = state.clone()
        ai_player = players[current_turn]
        ai_future = ai_executor.submit(_compute_ai_move, ai_player, state_snapshot)
        ai_expected_revision = state_revision
        ai_expected_turn = current_turn
        ai_expected_type = current_type

    def consume_ai_result_if_ready():
        nonlocal ai_future, ai_expected_revision, ai_expected_turn, ai_expected_type

        if ai_future is None or not ai_future.done():
            return

        expected_revision = ai_expected_revision
        expected_turn = ai_expected_turn
        expected_type = ai_expected_type

        try:
            move = ai_future.result()
        except Exception:
            move = None

        ai_future = None
        ai_expected_revision = None
        ai_expected_turn = None
        ai_expected_type = None

        if screen_mode != "playing" or state.game_over:
            return

        if expected_revision != state_revision:
            return

        if expected_turn is None or expected_type is None:
            return

        if state.turn != expected_turn:
            return

        if player_types.get(state.turn) != expected_type:
            return

        if move is not None and apply_move_and_track(move[0], move[1]):
            draw_current_game()
            if state.game_over:
                handle_finished_game()

    def render_menu():
        nonlocal menu_buttons
        show_fast_toggle = not is_human_type(player_types["X"]) and not is_human_type(player_types["O"])
        menu_buttons = ui.draw_menu(
            player_types["X"],
            player_types["O"],
            PLAYER_OPTIONS,
            rounds_input_text,
            rounds_input_active,
            show_fast_toggle,
            fast_simulation_enabled,
            open_dropdown,
            pygame.mouse.get_pos(),
        )

    def current_series_status() -> str | None:
        if series_total_rounds <= 1 or screen_mode != "playing":
            return None
        return (
            f"Turn:{state.turn} | "
            f"Player 1:{series_scores['X']} | "
            f"Player 2:{series_scores['O']} | "
            f"Draws:{series_scores['Draw']} | "
            f"Round:{series_current_round}/{series_total_rounds}"
        )

    def current_dashboard_lines() -> list[str]:
        lines = [
            f"Round: {series_current_round}/{series_total_rounds}",
            f"Player 1 wins: {series_scores['X']}",
            f"Player 2 wins: {series_scores['O']}",
            f"Draws: {series_scores['Draw']}",
        ]
        if screen_mode == "playing" and not state.game_over:
            lines.append(f"Current turn: {state.turn}")
        return lines

    def draw_current_game():
        if not match_has_human and fast_simulation_enabled:
            ui.set_fast_dashboard(True, "Fast Simulation", current_dashboard_lines())
            ui.draw_fast_dashboard()
        else:
            ui.set_fast_dashboard(False)
            ui.draw_game(current_series_status())

    def start_match():
        nonlocal players, screen_mode, open_dropdown, game_over_buttons, escape_menu_buttons
        nonlocal series_total_rounds, series_current_round, series_scores, series_active, match_has_human

        players = {
            "X": build_player("X", player_types["X"], state),
            "O": build_player("O", player_types["O"], state),
        }

        parsed_rounds = int(rounds_input_text) if rounds_input_text.isdigit() else 1
        series_total_rounds = max(1, parsed_rounds)
        series_current_round = 1
        series_scores = {
            "X": 0,
            "O": 0,
            "Draw": 0,
        }
        series_active = (
            series_total_rounds > 1
            and not is_human_type(player_types["X"])
            and not is_human_type(player_types["O"])
        )
        match_has_human = is_human_type(player_types["X"]) or is_human_type(player_types["O"])

        reset_state()
        screen_mode = "playing"
        open_dropdown = None
        game_over_buttons = None
        escape_menu_buttons = None
        draw_current_game()

    def handle_finished_game(render_round_reset: bool = True):
        nonlocal screen_mode, game_over_buttons, series_current_round, series_active

        if screen_mode != "playing" or not state.game_over:
            return

        if series_active:
            if state.status == "X wins":
                series_scores["X"] += 1
            elif state.status == "O wins":
                series_scores["O"] += 1
            else:
                series_scores["Draw"] += 1

            if series_current_round < series_total_rounds:
                series_current_round += 1
                reset_state()
                draw_current_game()
                if not render_round_reset:
                    pygame.event.pump()
                return

            series_active = False
            screen_mode = "game_over"
            series_title, series_lines = build_series_summary(player_types, series_scores)
            game_over_buttons = ui.draw_game_over(series_title, series_lines)
            return

        screen_mode = "game_over"
        game_over_buttons = ui.draw_game_over(build_winner_text(state.status, player_types))

    render_menu()

    while True:
        current_player = players[state.turn] if screen_mode == "playing" else None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ai_executor.shutdown(wait=False, cancel_futures=True)
                ui.close()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if screen_mode in ("playing", "game_over"):
                    if screen_mode == "game_over" and series_total_rounds > 1 and not series_active:
                        continue
                    escape_return_mode = screen_mode
                    screen_mode = "escape_menu"
                    game_over_buttons = None
                    escape_menu_buttons = ui.draw_escape_menu()
                elif screen_mode == "escape_menu":
                    screen_mode = escape_return_mode
                    escape_menu_buttons = None
                    if screen_mode == "game_over":
                        if series_total_rounds > 1 and not series_active:
                            series_title, series_lines = build_series_summary(player_types, series_scores)
                            game_over_buttons = ui.draw_game_over(series_title, series_lines)
                        else:
                            game_over_buttons = ui.draw_game_over(build_winner_text(state.status, player_types))
                    else:
                        draw_current_game()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and screen_mode == "playing":
                reset_state()
                game_over_buttons = None
                draw_current_game()

            if event.type == pygame.KEYDOWN and screen_mode == "menu" and rounds_input_active:
                if event.key == pygame.K_BACKSPACE:
                    rounds_input_text = rounds_input_text[:-1]
                    render_menu()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    rounds_input_active = False
                    render_menu()
                elif event.unicode.isdigit():
                    if len(rounds_input_text) < 6:
                        rounds_input_text += event.unicode
                        render_menu()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if screen_mode == "menu":
                    rounds_input_active = False
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
                        render_menu()
                    elif (
                        menu_buttons["rounds_input"] is not None
                        and menu_buttons["rounds_input"].collidepoint(mx, my)
                    ):
                        rounds_input_active = True
                        render_menu()
                    elif menu_buttons["x_dropdown"].collidepoint(mx, my):
                        open_dropdown = None if open_dropdown == "X" else "X"
                        render_menu()
                    elif menu_buttons["o_dropdown"].collidepoint(mx, my):
                        open_dropdown = None if open_dropdown == "O" else "O"
                        render_menu()
                    elif (
                        menu_buttons["fast_toggle"] is not None
                        and menu_buttons["fast_toggle"].collidepoint(mx, my)
                    ):
                        fast_simulation_enabled = not fast_simulation_enabled
                        render_menu()
                    elif menu_buttons["start"].collidepoint(mx, my):
                        start_match()
                    else:
                        open_dropdown = None
                        render_menu()

                elif (
                    screen_mode == "playing"
                    and not state.game_over
                    and is_human_type(player_types[state.turn])
                ):
                    cell = ui.pixel_to_cell(mx, my)
                    if cell is not None and apply_move_and_track(cell[0], cell[1]):
                        draw_current_game()
                        if state.game_over:
                            handle_finished_game()

                elif screen_mode == "game_over" and game_over_buttons is not None:
                    if game_over_buttons["play_again"].collidepoint(mx, my):
                        start_match()
                    elif game_over_buttons["main_menu"].collidepoint(mx, my):
                        reset_state()
                        screen_mode = "menu"
                        open_dropdown = None
                        game_over_buttons = None
                        series_active = False
                        render_menu()

                elif screen_mode == "escape_menu" and escape_menu_buttons is not None:
                    if escape_menu_buttons["resume"].collidepoint(mx, my):
                        screen_mode = escape_return_mode
                        escape_menu_buttons = None
                        if screen_mode == "game_over":
                            game_over_buttons = ui.draw_game_over(build_winner_text(state.status, player_types))
                        else:
                            draw_current_game()
                    elif escape_menu_buttons["reset"].collidepoint(mx, my):
                        start_match()
                    elif escape_menu_buttons["main_menu"].collidepoint(mx, my):
                        reset_state()
                        screen_mode = "menu"
                        open_dropdown = None
                        escape_menu_buttons = None
                        series_active = False
                        render_menu()

        if screen_mode == "menu":
            render_menu()

        consume_ai_result_if_ready()

        if screen_mode == "playing" and state.game_over and game_over_buttons is None:
            handle_finished_game()

        queue_ai_move_if_needed()

        ui.tick()


if __name__ == "__main__":
    run()