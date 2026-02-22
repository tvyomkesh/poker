"""ASCII card graphics for the poker game."""

from typing import List, Tuple
import curses
from game.cards import Card
from .colors import Colors


class CardRenderer:
    """Renders playing cards as ASCII art."""

    # Card dimensions
    CARD_WIDTH = 7
    CARD_HEIGHT = 5

    # Card templates
    CARD_TOP = "\u250c\u2500\u2500\u2500\u2500\u2500\u2510"      # ┌─────┐
    CARD_BOTTOM = "\u2514\u2500\u2500\u2500\u2500\u2500\u2518"  # └─────┘
    CARD_SIDE = "\u2502"                                         # │
    CARD_EMPTY = "\u2502     \u2502"                             # │     │

    # Face-down card pattern
    CARD_BACK_PATTERN = [
        "\u250c\u2500\u2500\u2500\u2500\u2500\u2510",  # ┌─────┐
        "\u2502\u2591\u2591\u2591\u2591\u2591\u2502",  # │░░░░░│
        "\u2502\u2591\u2591\u2591\u2591\u2591\u2502",  # │░░░░░│
        "\u2502\u2591\u2591\u2591\u2591\u2591\u2502",  # │░░░░░│
        "\u2514\u2500\u2500\u2500\u2500\u2500\u2518",  # └─────┘
    ]

    # Mini card for compact display
    MINI_CARD_WIDTH = 4
    MINI_CARD_HEIGHT = 3

    @classmethod
    def get_card_lines(cls, card: Card) -> List[str]:
        """
        Get the ASCII art lines for a card.

        Args:
            card: The card to render

        Returns:
            List of strings representing each line
        """
        rank = card.rank_str
        suit = card.suit_symbol

        # Pad rank to 2 chars for alignment
        rank_left = rank.ljust(2)
        rank_right = rank.rjust(2)

        lines = [
            cls.CARD_TOP,
            f"{cls.CARD_SIDE}{rank_left}   {cls.CARD_SIDE}",
            f"{cls.CARD_SIDE}  {suit}  {cls.CARD_SIDE}",
            f"{cls.CARD_SIDE}   {rank_right}{cls.CARD_SIDE}",
            cls.CARD_BOTTOM,
        ]

        return lines

    @classmethod
    def get_face_down_lines(cls) -> List[str]:
        """Get ASCII art for a face-down card."""
        return cls.CARD_BACK_PATTERN.copy()

    @classmethod
    def get_mini_card(cls, card: Card) -> str:
        """Get a compact single-line representation of a card."""
        return f"[{card.rank_str}{card.suit_symbol}]"

    @classmethod
    def get_mini_face_down(cls) -> str:
        """Get a compact face-down card representation."""
        return "[??]"

    @classmethod
    def draw_card(cls, stdscr, y: int, x: int, card: Card):
        """
        Draw a card at the specified position.

        Args:
            stdscr: Curses window
            y: Top row position
            x: Left column position
            card: Card to draw
        """
        lines = cls.get_card_lines(card)
        color = Colors.get_card_color(card.is_red)

        for i, line in enumerate(lines):
            try:
                stdscr.addstr(y + i, x, line, color)
            except curses.error:
                pass

    @classmethod
    def draw_face_down_card(cls, stdscr, y: int, x: int):
        """
        Draw a face-down card at the specified position.

        Args:
            stdscr: Curses window
            y: Top row position
            x: Left column position
        """
        lines = cls.get_face_down_lines()
        color = Colors.pair(Colors.CARD_BACK)

        for i, line in enumerate(lines):
            try:
                stdscr.addstr(y + i, x, line, color)
            except curses.error:
                pass

    @classmethod
    def draw_cards_row(cls, stdscr, y: int, x: int, cards: List[Card],
                       face_down: bool = False, spacing: int = 1):
        """
        Draw multiple cards in a row.

        Args:
            stdscr: Curses window
            y: Top row position
            x: Starting left column position
            cards: List of cards to draw
            face_down: If True, draw all cards face down
            spacing: Space between cards
        """
        current_x = x
        for card in cards:
            if face_down:
                cls.draw_face_down_card(stdscr, y, current_x)
            else:
                cls.draw_card(stdscr, y, current_x, card)
            current_x += cls.CARD_WIDTH + spacing

    @classmethod
    def draw_community_cards(cls, stdscr, y: int, center_x: int,
                             cards: List[Card], revealed: int = 0):
        """
        Draw community cards centered, with some face-down.

        Args:
            stdscr: Curses window
            y: Top row position
            center_x: Center x position
            cards: List of 5 potential card slots
            revealed: Number of cards to show face-up (0-5)
        """
        total_width = 5 * cls.CARD_WIDTH + 4  # 5 cards + 4 gaps
        start_x = center_x - total_width // 2

        for i in range(5):
            card_x = start_x + i * (cls.CARD_WIDTH + 1)
            if i < revealed and i < len(cards):
                cls.draw_card(stdscr, y, card_x, cards[i])
            else:
                cls.draw_face_down_card(stdscr, y, card_x)

    @classmethod
    def draw_mini_cards(cls, stdscr, y: int, x: int, cards: List[Card],
                        face_down: bool = False):
        """
        Draw compact card representations.

        Args:
            stdscr: Curses window
            y: Row position
            x: Starting column
            cards: Cards to display
            face_down: Show as face-down
        """
        current_x = x
        for card in cards:
            if face_down:
                text = cls.get_mini_face_down()
                color = Colors.pair(Colors.CARD_BACK)
            else:
                text = cls.get_mini_card(card)
                color = Colors.get_card_color(card.is_red)

            try:
                stdscr.addstr(y, current_x, text, color)
            except curses.error:
                pass
            current_x += len(text) + 1

    @classmethod
    def get_cards_width(cls, count: int, spacing: int = 1) -> int:
        """Calculate total width needed for a row of cards."""
        if count == 0:
            return 0
        return count * cls.CARD_WIDTH + (count - 1) * spacing
