"""Main game display for Texas Hold'em Poker."""

import curses
import time
from typing import List, Optional, Dict
from game.poker import PokerGame, GamePhase
from game.player import Player, PlayerAction
from game.odds import OddsCalculator
from game.constants import (
    BOARD_MARGIN_X, BOARD_HEIGHT_PERCENT, LOG_LINES, BIG_BLIND
)
from .colors import Colors
from .card_art import CardRenderer


# Hand rankings for reference (best to worst)
HAND_RANKINGS = [
    ("Royal Flush", "A K Q J 10 same suit"),
    ("Straight Flush", "5 consecutive, same suit"),
    ("Four of a Kind", "4 cards same rank"),
    ("Full House", "3 of a kind + pair"),
    ("Flush", "5 cards same suit"),
    ("Straight", "5 consecutive cards"),
    ("Three of a Kind", "3 cards same rank"),
    ("Two Pair", "2 different pairs"),
    ("One Pair", "2 cards same rank"),
    ("High Card", "Highest card wins"),
]


class GameDisplay:
    """Handles all rendering for the poker game."""

    def __init__(self, stdscr):
        """
        Initialize the game display.

        Args:
            stdscr: Curses standard screen
        """
        self.stdscr = stdscr
        self.log_messages: List[str] = []
        self.max_log_lines = LOG_LINES
        self.bot_difficulty = None  # Set by main app
        self.num_players = 2  # Default, updated by main app

        # Initialize colors
        Colors.init_colors()

        # Configure curses
        curses.curs_set(0)  # Hide cursor
        stdscr.keypad(True)
        stdscr.nodelay(False)
        stdscr.timeout(-1)

        # Calculate dimensions
        self._update_dimensions()

    def _update_dimensions(self):
        """Calculate board dimensions based on terminal size."""
        self.term_height, self.term_width = self.stdscr.getmaxyx()

        # Right panel width (for odds and rankings)
        self.right_panel_width = 32
        self.has_right_panel = self.term_width >= 110  # Only show if wide enough

        # Board takes width minus margins and right panel
        self.board_left = BOARD_MARGIN_X
        if self.has_right_panel:
            self.board_width = self.term_width - (BOARD_MARGIN_X * 2) - self.right_panel_width - 1
            self.right_panel_left = self.board_left + self.board_width + 2
        else:
            self.board_width = self.term_width - (BOARD_MARGIN_X * 2)
            self.right_panel_left = 0

        # Board takes percentage of height, leaving room for log
        self.board_top = 0
        self.board_height = int(self.term_height * BOARD_HEIGHT_PERCENT)
        self.board_bottom = self.board_top + self.board_height - 1

        # Center X for placing elements (center of main board only)
        self.center_x = self.board_left + self.board_width // 2

        # Calculate vertical zones within the board
        inner_height = self.board_height - 2  # Minus top/bottom borders

        # Layout zones with proper spacing to avoid overlaps:
        # - Top bots: near top
        # - Phase indicator + community cards: middle
        # - Human: near bottom (with space for showdown message above)
        self.bot_y = self.board_top + 2
        # Push community cards down to make room for top bot cards + phase indicator
        # Bot cards take ~8 lines (info + gap + 5-line cards), plus 2 for phase indicator
        self.community_y = self.board_top + int(inner_height * 0.45)
        self.pot_y = self.community_y + CardRenderer.CARD_HEIGHT + 2
        # Human cards closer to bottom, leaving room for showdown message
        self.human_y = self.board_bottom - CardRenderer.CARD_HEIGHT - 3

        # Log area starts after board
        self.log_start_y = self.board_bottom + 2

        # Player positions will be calculated dynamically
        self.player_positions = {}

    def _calculate_player_positions(self, num_players: int) -> Dict[int, tuple]:
        """
        Calculate (y, x, alignment) for each player position.

        Returns dict: player_index -> (info_y, cards_y, x, alignment)
        Info takes 2 lines (name + chips), then cards below.
        Layout:
        - 2 players: Human (bottom), Bot1 (top)
        - 3 players: Human (bottom), Bot1 (top-left), Bot2 (top-right)
        - 4 players: Human (bottom), Bot1 (left), Bot2 (top), Bot3 (right)
        """
        positions = {}

        # Human is always at the bottom
        # Cards at human_y, info 2 lines above (name, chips/action)
        human_info_y = self.human_y - 2
        positions[0] = (human_info_y, self.human_y, self.center_x, 'center')

        if num_players == 2:
            # Classic heads-up: bot at top center
            positions[1] = (self.bot_y, self.bot_y + 3, self.center_x, 'center')

        elif num_players == 3:
            # 3-way: bots at top-left and top-right
            offset = self.board_width // 4
            positions[1] = (self.bot_y, self.bot_y + 3, self.center_x - offset, 'center')
            positions[2] = (self.bot_y, self.bot_y + 3, self.center_x + offset, 'center')

        elif num_players == 4:
            # 4-way: bot1 left, bot2 top, bot3 right
            side_y = self.community_y - 3  # Position bots at sides
            left_x = self.board_left + 14
            right_x = self.board_left + self.board_width - 14

            positions[1] = (side_y, side_y + 3, left_x, 'left')
            positions[2] = (self.bot_y, self.bot_y + 3, self.center_x, 'center')
            positions[3] = (side_y, side_y + 3, right_x, 'right')

        return positions

    def add_log(self, message: str):
        """Add a message to the action log."""
        self.log_messages.append(message)
        # Keep more messages for scrolling
        if len(self.log_messages) > 50:
            self.log_messages.pop(0)

    def clear_log(self):
        """Clear the action log."""
        self.log_messages = []

    def draw_border(self):
        """Draw the game board border."""
        color = Colors.pair(Colors.BORDER) | curses.A_BOLD

        # Top border
        top_line = "\u2554" + "\u2550" * (self.board_width - 2) + "\u2557"
        try:
            self.stdscr.addstr(self.board_top, self.board_left, top_line, color)
        except curses.error:
            pass

        # Side borders
        for y in range(self.board_top + 1, self.board_bottom):
            try:
                self.stdscr.addstr(y, self.board_left, "\u2551", color)
                self.stdscr.addstr(y, self.board_left + self.board_width - 1, "\u2551", color)
            except curses.error:
                pass

        # Bottom border
        bottom_line = "\u255a" + "\u2550" * (self.board_width - 2) + "\u255d"
        try:
            self.stdscr.addstr(self.board_bottom, self.board_left, bottom_line, color)
        except curses.error:
            pass

    def draw_title(self, game: PokerGame):
        """Draw the game title with difficulty."""
        # Main title
        title = f" TEXAS HOLD'EM - Hand #{game.hand_number} "
        x = self.center_x - len(title) // 2
        try:
            self.stdscr.addstr(self.board_top, x, title,
                               Colors.pair(Colors.TITLE) | curses.A_BOLD)
        except curses.error:
            pass

        # Difficulty indicator on the right
        if self.bot_difficulty:
            diff_name = self.bot_difficulty.value
            diff_str = f"[{diff_name}]"
            diff_x = self.board_left + self.board_width - len(diff_str) - 2
            try:
                if diff_name == "Hard":
                    color = Colors.pair(Colors.CARD_RED)
                elif diff_name == "Medium":
                    color = Colors.pair(Colors.CHIPS)
                else:
                    color = Colors.pair(Colors.PROMPT)
                self.stdscr.addstr(self.board_top, diff_x, diff_str, color | curses.A_BOLD)
            except curses.error:
                pass

    def draw_player_info(self, player: Player, y: int, is_current: bool,
                         is_winner: bool = False, center_x: int = None,
                         alignment: str = 'center'):
        """Draw player name, chips, and bet info."""
        if center_x is None:
            center_x = self.center_x

        # Player name and status
        if is_winner:
            color = Colors.pair(Colors.WINNER) | curses.A_BOLD
            status = " WINNER!"
        elif is_current:
            color = Colors.pair(Colors.PLAYER_ACTIVE) | curses.A_BOLD
            status = " *"
        else:
            color = Colors.pair(Colors.PLAYER_WAITING)
            status = ""

        # Build position markers: D=Dealer, SB=Small Blind, BB=Big Blind
        position_marks = []
        if player.is_dealer:
            position_marks.append("D")
        if player.is_sb:
            position_marks.append("SB")
        if player.is_bb:
            position_marks.append("BB")
        position_str = " [" + "/".join(position_marks) + "]" if position_marks else ""
        info = f"{player.name}{position_str}{status}"

        # Position based on alignment
        if alignment == 'center':
            info_x = center_x - len(info) // 2
        elif alignment == 'left':
            info_x = center_x
        else:  # right
            info_x = center_x - len(info)

        try:
            self.stdscr.addstr(y, info_x, info, color)
        except curses.error:
            pass

        # Build display line: (Chips: $X) (Bet: $Y) or (Chips: $X) (Action)
        # Chips in green, bet/action in yellow (with red for fold)
        # Only show bet if no action yet; once action is taken, show action instead
        chips_part = f"(${player.chips})"
        if player.last_action:
            bet_part = ""
            action_part = f"({player.last_action})"
        elif player.current_bet > 0:
            bet_part = f"(Bet: ${player.current_bet})"
            action_part = ""
        else:
            bet_part = ""
            action_part = ""

        # Calculate full string for positioning
        full_str = chips_part
        if bet_part:
            full_str += " " + bet_part
        if action_part:
            full_str += " " + action_part

        if alignment == 'center':
            start_x = center_x - len(full_str) // 2
        elif alignment == 'left':
            start_x = center_x
        else:  # right
            start_x = center_x - len(full_str)

        # Draw chips in green (CHIPS color)
        try:
            self.stdscr.addstr(y + 1, start_x, chips_part, Colors.pair(Colors.CHIPS))
        except curses.error:
            pass

        # Determine color for bet and action (yellow, or red for fold)
        activity_color = Colors.pair(Colors.PLAYER_ACTIVE)  # Yellow
        if player.last_action and "Folded" in player.last_action:
            activity_color = Colors.pair(Colors.CARD_RED)

        # Draw bet in activity color
        if bet_part:
            bet_x = start_x + len(chips_part) + 1
            try:
                self.stdscr.addstr(y + 1, bet_x, bet_part, activity_color)
            except curses.error:
                pass

        # Draw action in same activity color
        if action_part:
            action_x = start_x + len(chips_part) + 1
            if bet_part:
                action_x += len(bet_part) + 1

            try:
                self.stdscr.addstr(y + 1, action_x, action_part, activity_color)
            except curses.error:
                pass

    def draw_player_cards(self, player: Player, y: int, show_cards: bool,
                          center_x: int = None, alignment: str = 'center'):
        """Draw player's hole cards using full-size card graphics."""
        if not player.hole_cards:
            return

        if center_x is None:
            center_x = self.center_x

        # Calculate position based on alignment
        total_width = CardRenderer.get_cards_width(2, spacing=2)

        if alignment == 'center':
            start_x = center_x - total_width // 2
        elif alignment == 'left':
            start_x = center_x
        else:  # right
            start_x = center_x - total_width

        if show_cards:
            CardRenderer.draw_cards_row(
                self.stdscr, y, start_x,
                player.hole_cards, face_down=False, spacing=2
            )
        else:
            CardRenderer.draw_face_down_card(self.stdscr, y, start_x)
            CardRenderer.draw_face_down_card(
                self.stdscr, y, start_x + CardRenderer.CARD_WIDTH + 2
            )

    def draw_community_cards(self, game: PokerGame):
        """Draw the community cards in the center."""
        y = self.community_y

        # Determine how many cards to reveal
        if game.phase == GamePhase.PRE_FLOP:
            revealed = 0
        elif game.phase == GamePhase.FLOP:
            revealed = 3
        elif game.phase == GamePhase.TURN:
            revealed = 4
        else:
            revealed = 5

        CardRenderer.draw_community_cards(
            self.stdscr, y, self.center_x,
            game.community_cards, revealed
        )

    def draw_pot(self, game: PokerGame):
        """Draw the pot amount."""
        pot_str = f"\u2b50 POT: ${game.pot} \u2b50"  # Star decorations
        pot_x = self.center_x - len(pot_str) // 2

        try:
            self.stdscr.addstr(self.pot_y, pot_x, pot_str,
                               Colors.pair(Colors.POT) | curses.A_BOLD)
        except curses.error:
            pass

    def draw_phase_indicator(self, game: PokerGame):
        """Draw the current game phase just above community cards."""
        phase_names = {
            GamePhase.PRE_FLOP: "PRE-FLOP",
            GamePhase.FLOP: "FLOP",
            GamePhase.TURN: "TURN",
            GamePhase.RIVER: "RIVER",
            GamePhase.SHOWDOWN: "SHOWDOWN",
        }
        phase_name = phase_names.get(game.phase, "")
        if phase_name:
            phase_str = f"[ {phase_name} ]"
            x = self.center_x - len(phase_str) // 2
            y = self.community_y - 1  # Just 1 line above community cards
            try:
                self.stdscr.addstr(y, x, phase_str,
                                   Colors.pair(Colors.TITLE))
            except curses.error:
                pass

    def draw_controls(self, game: PokerGame):
        """Draw the keyboard controls in the board."""
        y = self.board_bottom - 1

        if game.phase == GamePhase.GAME_OVER:
            controls = "  [R] Restart Game    [Q] Quit  "
        elif game.phase == GamePhase.SHOWDOWN:
            controls = "  [N] Next Hand    [R] Restart    [Q] Quit  "
        else:
            valid = game.get_valid_actions()
            parts = []

            if PlayerAction.CHECK in valid:
                parts.append("[C] Check")
            if PlayerAction.CALL in valid:
                to_call = game.current_player.amount_to_call(game.current_bet)
                parts.append(f"[C] Call ${to_call}")
            if PlayerAction.RAISE in valid:
                parts.append("[R] Raise")
            if PlayerAction.FOLD in valid:
                parts.append("[F] Fold")
            parts.append("[Q] Quit")

            controls = "    ".join(parts)

        x = self.center_x - len(controls) // 2
        try:
            self.stdscr.addstr(y, x, controls, Colors.pair(Colors.SHORTCUT) | curses.A_BOLD)
        except curses.error:
            pass

    def draw_log(self):
        """Draw the action log at the bottom."""
        # Calculate how many lines we can show
        available_lines = self.term_height - self.log_start_y - 1
        lines_to_show = min(available_lines, len(self.log_messages))

        # Show most recent messages
        recent_messages = self.log_messages[-lines_to_show:] if lines_to_show > 0 else []

        # Draw header
        try:
            header = " Action Log "
            header_line = "\u2500" * 3 + header + "\u2500" * (self.board_width - len(header) - 3)
            self.stdscr.addstr(self.log_start_y - 1, self.board_left, header_line,
                               Colors.pair(Colors.LOG))
        except curses.error:
            pass

        for i, msg in enumerate(recent_messages):
            y = self.log_start_y + i
            if y < self.term_height - 1:
                # Truncate if too long
                max_len = self.board_width - 4
                display_msg = msg[:max_len] if len(msg) > max_len else msg
                try:
                    self.stdscr.addstr(y, self.board_left + 1, f"> {display_msg}",
                                       Colors.pair(Colors.LOG))
                except curses.error:
                    pass

    def draw_showdown_info(self, game: PokerGame):
        """Draw showdown information with celebration."""
        if game.phase != GamePhase.SHOWDOWN:
            return

        y = self.pot_y + 2

        if game.winner:
            # Find winner's position and draw celebration there
            for idx, player in enumerate(game.players):
                if player == game.winner:
                    info_y, cards_y, pos_x, alignment = self.player_positions.get(idx, (0, 0, self.center_x, 'center'))
                    self._draw_win_celebration(cards_y, pos_x, alignment)
                    break
            msg = f"{game.winner.name} won with {game.winning_description}"
        else:
            msg = game.winning_description

        msg_x = self.center_x - len(msg) // 2
        try:
            self.stdscr.addstr(y, msg_x, msg,
                               Colors.pair(Colors.WINNER) | curses.A_BOLD)
        except curses.error:
            pass

    def _draw_win_celebration(self, cards_y: int, center_x: int, alignment: str):
        """Draw celebration sparkles around the winner's cards."""
        sparkles = ["\u2728", "\u2b50", "\u2605", "\u2606", "\u2734", "\u2733"]  # ✨ ⭐ ★ ☆ ✴ ✳

        # Calculate card area width (2 cards + spacing)
        card_area_width = CardRenderer.CARD_WIDTH * 2 + 2

        if alignment == 'center':
            left_x = center_x - card_area_width // 2 - 3
            right_x = center_x + card_area_width // 2 + 2
        elif alignment == 'left':
            left_x = center_x - 3
            right_x = center_x + card_area_width + 2
        else:  # right
            left_x = center_x - card_area_width - 3
            right_x = center_x + 2

        # Draw sparkles around the winner's cards
        positions = [
            (cards_y - 1, left_x),
            (cards_y - 1, right_x),
            (cards_y + 1, left_x - 2),
            (cards_y + 1, right_x + 2),
            (cards_y + 3, left_x),
            (cards_y + 3, right_x),
            (cards_y + CardRenderer.CARD_HEIGHT, left_x),
            (cards_y + CardRenderer.CARD_HEIGHT, right_x),
        ]

        frame = int(time.time() * 4) % len(sparkles)  # Animate sparkles

        for i, (py, px) in enumerate(positions):
            sparkle = sparkles[(frame + i) % len(sparkles)]
            color = Colors.pair(Colors.CHIPS) if i % 2 == 0 else Colors.pair(Colors.WINNER)
            try:
                self.stdscr.addstr(py, px, sparkle, color | curses.A_BOLD)
            except curses.error:
                pass

    def draw_game_over(self, game: PokerGame):
        """Draw game over screen."""
        y = self.center_x
        center_y = self.board_top + self.board_height // 2 - 3

        # Find winner - the player with the most chips (who won the match)
        winner = None
        max_chips = 0
        for player in game.players:
            if player.chips > max_chips:
                max_chips = player.chips
                winner = player

        if winner:
            msg1 = "\u2605 GAME OVER \u2605"
            msg2 = f"{winner.name} won the match!"
            msg3 = "[R] Restart  [Q] Quit"

            try:
                self.stdscr.addstr(center_y, self.center_x - len(msg1) // 2, msg1,
                                   Colors.pair(Colors.TITLE) | curses.A_BOLD)
                self.stdscr.addstr(center_y + 3, self.center_x - len(msg2) // 2, msg2,
                                   Colors.pair(Colors.WINNER) | curses.A_BOLD)
                self.stdscr.addstr(center_y + 6, self.center_x - len(msg3) // 2, msg3,
                                   Colors.pair(Colors.SHORTCUT))
            except curses.error:
                pass

    def draw_decorative_elements(self):
        """Draw decorative elements on the table."""
        # Draw corner decorations
        corners = [
            (self.board_top + 2, self.board_left + 3, "\u2663"),
            (self.board_top + 2, self.board_left + self.board_width - 4, "\u2660"),
            (self.board_bottom - 2, self.board_left + 3, "\u2665"),
            (self.board_bottom - 2, self.board_left + self.board_width - 4, "\u2666"),
        ]

        for y, x, symbol in corners:
            try:
                color = Colors.pair(Colors.CARD_RED) if symbol in ("\u2665", "\u2666") else Colors.pair(Colors.BORDER)
                self.stdscr.addstr(y, x, symbol, color)
            except curses.error:
                pass

    def draw_right_panel(self, game: PokerGame):
        """Draw the right panel with odds and hand rankings."""
        if not self.has_right_panel:
            return

        x = self.right_panel_left
        panel_width = self.right_panel_width - 1

        # Draw panel border
        try:
            # Top border
            self.stdscr.addstr(self.board_top, x, "\u2554" + "\u2550" * (panel_width - 2) + "\u2557",
                               Colors.pair(Colors.BORDER))
            # Side borders
            for y in range(self.board_top + 1, self.board_bottom):
                self.stdscr.addstr(y, x, "\u2551", Colors.pair(Colors.BORDER))
                self.stdscr.addstr(y, x + panel_width - 1, "\u2551", Colors.pair(Colors.BORDER))
            # Bottom border
            self.stdscr.addstr(self.board_bottom, x, "\u255a" + "\u2550" * (panel_width - 2) + "\u255d",
                               Colors.pair(Colors.BORDER))
        except curses.error:
            pass

        # Draw hand probabilities (top section)
        self._draw_probabilities(game, x + 2, self.board_top + 1, panel_width - 4)

        # Draw separator
        sep_y = self.board_top + 12
        try:
            self.stdscr.addstr(sep_y, x, "\u255f" + "\u2500" * (panel_width - 2) + "\u2562",
                               Colors.pair(Colors.BORDER))
        except curses.error:
            pass

        # Draw hand rankings (bottom section)
        self._draw_hand_rankings(x + 2, sep_y + 1, panel_width - 4)

    def _draw_probabilities(self, game: PokerGame, x: int, y: int, width: int):
        """Draw hand probability analysis."""
        human = game.players[0]

        # Title
        title = " YOUR ODDS "
        try:
            self.stdscr.addstr(y, x, title, Colors.pair(Colors.TITLE) | curses.A_BOLD)
        except curses.error:
            pass

        y += 2

        if not human.hole_cards or game.phase == GamePhase.WAITING:
            try:
                self.stdscr.addstr(y, x, "Waiting for cards...", Colors.pair(Colors.LOG))
            except curses.error:
                pass
            return

        # Calculate probabilities
        probs = OddsCalculator.calculate_probabilities(
            human.hole_cards, game.community_cards
        )

        # Calculate win probability (considering number of opponents)
        num_opponents = len(game.players) - 1
        win_prob = OddsCalculator.calculate_win_probability(
            human.hole_cards, game.community_cards, num_opponents=num_opponents
        )

        # Show win probability first
        try:
            win_label = f"Win: {win_prob:.1f}%"
            bar_width = width - len(win_label) - 2
            filled = int((win_prob / 100) * bar_width)
            bar = "\u2588" * filled + "\u2591" * (bar_width - filled)

            if win_prob >= 60:
                color = Colors.pair(Colors.WINNER)
            elif win_prob >= 40:
                color = Colors.pair(Colors.CHIPS)
            else:
                color = Colors.pair(Colors.CARD_RED)

            self.stdscr.addstr(y, x, win_label, color | curses.A_BOLD)
            self.stdscr.addstr(y, x + len(win_label) + 1, bar, color)
        except curses.error:
            pass

        y += 2

        # Show hand probabilities
        # Map internal names to display names
        display_names = {
            'ROYAL_FLUSH': 'Royal Flush',
            'STRAIGHT_FLUSH': 'Str. Flush',
            'FOUR_OF_A_KIND': 'Four of Kind',
            'FULL_HOUSE': 'Full House',
            'FLUSH': 'Flush',
            'STRAIGHT': 'Straight',
            'THREE_OF_A_KIND': 'Three of Kind',
            'TWO_PAIR': 'Two Pair',
            'ONE_PAIR': 'One Pair',
            'HIGH_CARD': 'High Card',
        }

        # Sort by probability descending
        sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)

        shown = 0
        for hand_name, prob in sorted_probs:
            if shown >= 6:  # Limit to 6 hands
                break

            display = display_names.get(hand_name, hand_name)
            try:
                # Truncate display name if needed
                max_name_len = width - 8
                if len(display) > max_name_len:
                    display = display[:max_name_len-1] + "."

                prob_str = f"{prob:5.1f}%"
                line = f"{display:<{width-7}}{prob_str}"

                if prob >= 50:
                    color = Colors.pair(Colors.WINNER)
                elif prob >= 20:
                    color = Colors.pair(Colors.CHIPS)
                else:
                    color = Colors.pair(Colors.PROMPT)

                self.stdscr.addstr(y, x, line, color)
                y += 1
                shown += 1
            except curses.error:
                pass

    def _draw_hand_rankings(self, x: int, y: int, width: int):
        """Draw hand rankings reference."""
        # Title
        title = " HAND RANKINGS "
        try:
            self.stdscr.addstr(y, x, title, Colors.pair(Colors.TITLE) | curses.A_BOLD)
        except curses.error:
            pass

        y += 1

        for i, (hand_name, description) in enumerate(HAND_RANKINGS):
            try:
                # Alternate colors for readability
                if i < 5:
                    color = Colors.pair(Colors.WINNER)  # Top 5 hands
                else:
                    color = Colors.pair(Colors.PROMPT)  # Lower hands

                # Format: rank number + hand name
                rank_num = f"{i+1:2}."
                line = f"{rank_num} {hand_name}"

                self.stdscr.addstr(y, x, line, color)
                y += 1
            except curses.error:
                pass

    def render(self, game: PokerGame):
        """Render the full game state."""
        self._update_dimensions()
        self.num_players = len(game.players)
        self.player_positions = self._calculate_player_positions(self.num_players)
        self.stdscr.clear()

        # Draw border and title
        self.draw_border()
        self.draw_title(game)
        self.draw_decorative_elements()

        if game.phase == GamePhase.GAME_OVER:
            self.draw_game_over(game)
        else:
            is_showdown = game.phase == GamePhase.SHOWDOWN
            human = game.players[0]

            # Draw all players at their positions
            for idx, player in enumerate(game.players):
                info_y, cards_y, pos_x, alignment = self.player_positions[idx]
                is_current = (game.current_player == player and not is_showdown)
                is_winner = (game.winner == player)
                is_human = (idx == 0)

                # Draw player info
                self.draw_player_info(
                    player, info_y,
                    is_current=is_current,
                    is_winner=is_winner,
                    center_x=pos_x,
                    alignment=alignment
                )

                # Draw cards (human always shown, others only at showdown)
                show_cards = is_human or is_showdown
                self.draw_player_cards(
                    player, cards_y,
                    show_cards=show_cards,
                    center_x=pos_x,
                    alignment=alignment
                )

            # Phase indicator
            self.draw_phase_indicator(game)

            # Community cards (center)
            self.draw_community_cards(game)

            # Pot
            self.draw_pot(game)

            # Showdown info
            self.draw_showdown_info(game)

            # Controls
            self.draw_controls(game)

        # Right panel with odds and rankings
        self.draw_right_panel(game)

        # Action log (scrolling area at bottom)
        self.draw_log()

        self.stdscr.refresh()

    def get_raise_amount(self, game: PokerGame) -> Optional[int]:
        """Prompt user for raise amount."""
        y = self.board_bottom - 2
        x = self.board_left + 4

        player = game.current_player
        to_call = player.amount_to_call(game.current_bet)
        min_raise = game.min_raise
        # Max raise is chips remaining AFTER calling
        max_raise = player.chips - to_call

        if to_call > 0:
            prompt = f"Raise amount (call ${to_call} + raise ${min_raise}-${max_raise}, 'a'=all-in): "
        else:
            prompt = f"Bet amount (${min_raise}-${max_raise}, 'a'=all-in, ESC=cancel): "

        try:
            # Clear the line
            self.stdscr.addstr(y, x, " " * (self.board_width - 8))
            self.stdscr.addstr(y, x, prompt, Colors.pair(Colors.PROMPT))
        except curses.error:
            pass

        curses.curs_set(1)  # Show cursor

        try:
            self.stdscr.move(y, x + len(prompt))
            self.stdscr.refresh()
            input_str = ""

            while True:
                ch = self.stdscr.getch()
                if ch == ord('\n') or ch == curses.KEY_ENTER or ch == 10:
                    break
                elif ch == 27:  # ESC
                    return None
                elif ch == ord('a') or ch == ord('A'):
                    return max_raise
                elif ch == curses.KEY_BACKSPACE or ch == 127 or ch == 8:
                    if input_str:
                        input_str = input_str[:-1]
                        cy, cx = self.stdscr.getyx()
                        self.stdscr.move(cy, cx - 1)
                        self.stdscr.delch()
                        self.stdscr.refresh()
                elif 48 <= ch <= 57:  # Digits 0-9
                    input_str += chr(ch)
                    self.stdscr.addch(ch)
                    self.stdscr.refresh()

            if not input_str:
                return None

            amount = int(input_str)
            if amount < min_raise:
                amount = min_raise
            if amount > max_raise:
                amount = max_raise

            return amount

        except (ValueError, curses.error):
            return None
        finally:
            curses.curs_set(0)  # Hide cursor

    def show_message(self, message: str, wait: bool = True):
        """Display a temporary message."""
        y = self.board_bottom - 2
        x = self.board_left + 4

        try:
            self.stdscr.addstr(y, x, message, Colors.pair(Colors.PROMPT))
            self.stdscr.refresh()
        except curses.error:
            pass

        if wait:
            self.stdscr.getch()
