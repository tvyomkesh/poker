"""Color definitions for the poker game UI."""

import curses


class Colors:
    """Color pair definitions for the game."""

    # Color pair IDs
    DEFAULT = 0
    CARD_BLACK = 1       # Black card text (spades, clubs)
    CARD_RED = 2         # Red card text (hearts, diamonds)
    TABLE_FELT = 3       # Green felt background
    POT = 4              # Pot display (cyan)
    PLAYER_ACTIVE = 5    # Active player (yellow)
    PLAYER_WAITING = 6   # Waiting player (white)
    WINNER = 7           # Winner highlight (green)
    CARD_BACK = 8        # Face-down card
    BORDER = 9           # Table border
    PROMPT = 10          # Input prompt
    LOG = 11             # Action log
    TITLE = 12           # Title/header
    CHIPS = 13           # Chip count
    SHORTCUT = 14        # Keyboard shortcuts

    _initialized = False

    @classmethod
    def init_colors(cls):
        """Initialize color pairs. Must be called after curses.initscr()."""
        if cls._initialized:
            return

        curses.start_color()
        curses.use_default_colors()

        # Define color pairs (foreground, background)
        # -1 means default/transparent

        # Card colors
        curses.init_pair(cls.CARD_BLACK, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(cls.CARD_RED, curses.COLOR_RED, curses.COLOR_WHITE)

        # Table felt (dark green background)
        if curses.can_change_color():
            # Custom dark green
            curses.init_color(20, 0, 400, 0)  # Dark green
            curses.init_pair(cls.TABLE_FELT, curses.COLOR_WHITE, 20)
        else:
            curses.init_pair(cls.TABLE_FELT, curses.COLOR_WHITE, curses.COLOR_GREEN)

        # UI elements
        curses.init_pair(cls.POT, curses.COLOR_CYAN, -1)
        curses.init_pair(cls.PLAYER_ACTIVE, curses.COLOR_YELLOW, -1)
        curses.init_pair(cls.PLAYER_WAITING, curses.COLOR_WHITE, -1)
        curses.init_pair(cls.WINNER, curses.COLOR_GREEN, -1)
        curses.init_pair(cls.CARD_BACK, curses.COLOR_BLUE, curses.COLOR_WHITE)
        curses.init_pair(cls.BORDER, curses.COLOR_GREEN, -1)
        curses.init_pair(cls.PROMPT, curses.COLOR_WHITE, -1)
        curses.init_pair(cls.LOG, curses.COLOR_CYAN, -1)
        curses.init_pair(cls.TITLE, curses.COLOR_YELLOW, -1)
        curses.init_pair(cls.CHIPS, curses.COLOR_GREEN, -1)
        curses.init_pair(cls.SHORTCUT, curses.COLOR_MAGENTA, -1)

        cls._initialized = True

    @classmethod
    def get_card_color(cls, is_red: bool) -> int:
        """Get the appropriate color pair for a card."""
        return curses.color_pair(cls.CARD_RED if is_red else cls.CARD_BLACK)

    @classmethod
    def pair(cls, color_id: int) -> int:
        """Get the curses color pair attribute."""
        return curses.color_pair(color_id)
