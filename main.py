#!/usr/bin/env python3
"""
Texas Hold'em Poker - Terminal Edition
A curses-based poker game: Human vs 1-3 Bots
"""

import curses
import sys
import time
from game.player import HumanPlayer, PlayerAction
from game.bot import BotDifficulty, create_bot
from game.poker import PokerGame, GamePhase
from game.constants import MIN_TERMINAL_WIDTH, MIN_TERMINAL_HEIGHT
from ui.display import GameDisplay
from ui.colors import Colors


class PokerApp:
    """Main application class for the poker game."""

    def __init__(self, stdscr):
        """Initialize the poker application."""
        self.stdscr = stdscr
        self.running = True
        self.display = None
        self.human = None
        self.bots = []
        self.bot_count = 1
        self.game = None
        self.difficulty = BotDifficulty.MEDIUM

    def check_terminal_size(self) -> bool:
        """Check if terminal is large enough."""
        height, width = self.stdscr.getmaxyx()
        if width < MIN_TERMINAL_WIDTH or height < MIN_TERMINAL_HEIGHT:
            self.stdscr.clear()
            msg = f"Terminal too small. Need {MIN_TERMINAL_WIDTH}x{MIN_TERMINAL_HEIGHT}, "
            msg += f"got {width}x{height}"
            try:
                self.stdscr.addstr(0, 0, msg)
                self.stdscr.addstr(1, 0, "Please resize and press any key...")
                self.stdscr.refresh()
                self.stdscr.getch()
            except curses.error:
                pass
            return False
        return True

    def show_title_screen(self) -> bool:
        """Show title screen with difficulty selection."""
        Colors.init_colors()
        height, width = self.stdscr.getmaxyx()
        center_x = width // 2
        center_y = height // 2 - 8

        difficulties = [
            (BotDifficulty.EASY, "Easy", "Loose-passive fish - great for beginners"),
            (BotDifficulty.MEDIUM, "Medium", "Tight-aggressive regular - solid opponent"),
            (BotDifficulty.HARD, "Hard", "Near-GTO pro - very challenging"),
        ]
        selected = 2  # Default to Hard

        while True:
            self.stdscr.clear()

            # Title
            title = [
                "  _____                     _    _       _     _",
                " |_   _|____  ____ _ ___   | |  | | ___ | | __| | ___ _ __ ___",
                "   | | / _ \\ \\/ / _` / __| | |__| |/ _ \\| |/ _` |/ _ \\ '_ ` _ \\",
                "   | ||  __/>  < (_| \\__ \\ |  __  | (_) | | (_| |  __/ | | | | |",
                "   |_| \\___/_/\\_\\__,_|___/ |_|  |_|\\___/|_|\\__,_|\\___|_| |_| |_|",
            ]

            y = center_y - 3
            for line in title:
                x = center_x - len(line) // 2
                try:
                    self.stdscr.addstr(y, x, line, Colors.pair(Colors.TITLE) | curses.A_BOLD)
                except curses.error:
                    pass
                y += 1

            # Subtitle
            subtitle = "POKER TRAINING SIMULATOR"
            try:
                self.stdscr.addstr(y + 1, center_x - len(subtitle) // 2, subtitle,
                                   Colors.pair(Colors.CHIPS))
            except curses.error:
                pass

            # Difficulty selection
            y = center_y + 6
            try:
                self.stdscr.addstr(y, center_x - 12, "SELECT DIFFICULTY:",
                                   Colors.pair(Colors.PROMPT) | curses.A_BOLD)
            except curses.error:
                pass

            y += 2
            for i, (diff, name, desc) in enumerate(difficulties):
                if i == selected:
                    marker = ">"
                    color = Colors.pair(Colors.WINNER) | curses.A_BOLD
                else:
                    marker = " "
                    color = Colors.pair(Colors.PROMPT)

                line = f" {marker} [{i+1}] {name:8} - {desc}"
                try:
                    self.stdscr.addstr(y, center_x - 30, line, color)
                except curses.error:
                    pass
                y += 1

            # Instructions
            y += 2
            instructions = "[1/2/3] or [UP/DOWN] to select    [ENTER] to start    [Q] to quit"
            try:
                self.stdscr.addstr(y, center_x - len(instructions) // 2, instructions,
                                   Colors.pair(Colors.SHORTCUT))
            except curses.error:
                pass

            self.stdscr.refresh()

            # Handle input
            key = self.stdscr.getch()

            if key == ord('q') or key == ord('Q'):
                return False

            if key == ord('1'):
                selected = 0
            elif key == ord('2'):
                selected = 1
            elif key == ord('3'):
                selected = 2
            elif key == curses.KEY_UP:
                selected = (selected - 1) % 3
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % 3
            elif key in (ord('\n'), curses.KEY_ENTER, 10):
                self.difficulty = difficulties[selected][0]
                return True

    def show_bot_count_screen(self) -> bool:
        """Show screen to select number of bots (1-3)."""
        height, width = self.stdscr.getmaxyx()
        center_x = width // 2
        center_y = height // 2 - 4

        options = [
            (1, "1 Bot", "Classic heads-up poker"),
            (2, "2 Bots", "3-way action"),
            (3, "3 Bots", "Full 4-handed table"),
        ]
        selected = 2  # Default to 3 bots (4 players)

        while True:
            self.stdscr.clear()

            # Title
            title = "SELECT NUMBER OF OPPONENTS"
            try:
                self.stdscr.addstr(center_y - 2, center_x - len(title) // 2, title,
                                   Colors.pair(Colors.TITLE) | curses.A_BOLD)
            except curses.error:
                pass

            y = center_y + 1
            for i, (count, name, desc) in enumerate(options):
                marker = ">" if i == selected else " "
                color = Colors.pair(Colors.WINNER) | curses.A_BOLD if i == selected else Colors.pair(Colors.PROMPT)
                line = f" {marker} [{count}] {name:8} - {desc}"
                try:
                    self.stdscr.addstr(y, center_x - 25, line, color)
                except curses.error:
                    pass
                y += 1

            # Instructions
            y += 2
            instructions = "[1/2/3] or [UP/DOWN] to select    [ENTER] to continue    [Q] to quit"
            try:
                self.stdscr.addstr(y, center_x - len(instructions) // 2, instructions,
                                   Colors.pair(Colors.SHORTCUT))
            except curses.error:
                pass

            self.stdscr.refresh()

            key = self.stdscr.getch()

            if key == ord('q') or key == ord('Q'):
                return False
            elif key == ord('1'):
                selected = 0
            elif key == ord('2'):
                selected = 1
            elif key == ord('3'):
                selected = 2
            elif key == curses.KEY_UP:
                selected = (selected - 1) % 3
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % 3
            elif key in (ord('\n'), curses.KEY_ENTER, 10):
                self.bot_count = options[selected][0]
                return True

    def initialize_game(self):
        """Initialize the game with selected difficulty and bot count."""
        self.display = GameDisplay(self.stdscr)
        self.human = HumanPlayer("You")

        # Create multiple bots with unique names
        bot_names = ["Bot 1", "Bot 2", "Bot 3"]
        self.bots = []
        for i in range(self.bot_count):
            bot = create_bot(self.difficulty, name=bot_names[i])
            self.bots.append(bot)

        # Create game with all players (human first, then bots)
        all_players = [self.human] + self.bots
        self.game = PokerGame(
            players=all_players,
            on_action=self.display.add_log
        )

        # Store info in display for showing
        self.display.bot_difficulty = self.difficulty
        self.display.num_players = len(all_players)

    def handle_human_turn(self):
        """Handle input for human player's turn."""
        valid_actions = self.game.get_valid_actions()

        while True:
            self.display.render(self.game)

            key = self.stdscr.getch()

            if key == ord('q') or key == ord('Q'):
                self.running = False
                return

            if key == ord('c') or key == ord('C'):
                if PlayerAction.CHECK in valid_actions:
                    self.game.process_action(PlayerAction.CHECK)
                    return
                elif PlayerAction.CALL in valid_actions:
                    self.game.process_action(PlayerAction.CALL)
                    return

            elif key == ord('f') or key == ord('F'):
                if PlayerAction.FOLD in valid_actions:
                    self.game.process_action(PlayerAction.FOLD)
                    return

            elif key == ord('r') or key == ord('R'):
                if PlayerAction.RAISE in valid_actions:
                    amount = self.display.get_raise_amount(self.game)
                    if amount is not None:
                        self.game.process_action(PlayerAction.RAISE, amount)
                        return

    def handle_bot_turn(self):
        """Handle the current bot's turn with a slight delay for realism."""
        self.display.render(self.game)

        # Get the current bot player
        current_bot = self.game.current_player

        # Delay based on difficulty (harder = more "thinking")
        if self.difficulty == BotDifficulty.EASY:
            time.sleep(0.5)
        elif self.difficulty == BotDifficulty.MEDIUM:
            time.sleep(0.8)
        else:
            time.sleep(1.2)

        game_state = self.game.get_game_state()
        action, amount = current_bot.get_action(game_state)
        self.game.process_action(action, amount)

    def play_hand(self):
        """Play a complete hand."""
        self.game.start_hand()

        while self.game.phase not in (GamePhase.SHOWDOWN, GamePhase.GAME_OVER):
            if not self.running:
                return

            self.display.render(self.game)

            current = self.game.current_player

            if current == self.human:
                self.handle_human_turn()
            elif current in self.bots:
                self.handle_bot_turn()

        # Show final state
        self.display.render(self.game)

    def handle_showdown(self):
        """Handle post-showdown input."""
        while True:
            key = self.stdscr.getch()

            if key == ord('q') or key == ord('Q'):
                self.running = False
                return

            if key == ord('n') or key == ord('N'):
                if self.game.phase != GamePhase.GAME_OVER:
                    self.display.clear_log()
                    return

            if key == ord('r') or key == ord('R'):
                self.game.reset_game()
                self.display.clear_log()
                return

    def run(self):
        """Main game loop."""
        # Check terminal size
        while not self.check_terminal_size():
            pass

        # Show title screen and select difficulty
        if not self.show_title_screen():
            return

        # Select number of bots
        if not self.show_bot_count_screen():
            return

        # Initialize game with selected settings
        self.initialize_game()

        while self.running:
            self.play_hand()

            if not self.running:
                break

            # Show result and wait for next action
            self.display.render(self.game)
            self.handle_showdown()


def _curses_main(stdscr):
    """Curses wrapper main function."""
    curses.curs_set(0)
    app = PokerApp(stdscr)
    app.run()


def main():
    """Entry point for the poker game."""
    try:
        curses.wrapper(_curses_main)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
