"""Game constants and configuration for Texas Hold'em Poker."""

# Chip configuration
STARTING_CHIPS = 1000

# Blind structure
SMALL_BLIND = 10
BIG_BLIND = 20

# Minimum raise multiplier
MIN_RAISE_MULTIPLIER = 2

# Card suits with Unicode symbols
SUITS = {
    'spades': '\u2660',    # ♠
    'hearts': '\u2665',    # ♥
    'diamonds': '\u2666',  # ♦
    'clubs': '\u2663',     # ♣
}

# Suit colors (for display)
SUIT_COLORS = {
    'spades': 'black',
    'hearts': 'red',
    'diamonds': 'red',
    'clubs': 'black',
}

# Card ranks (2-14, where 11=J, 12=Q, 13=K, 14=A)
RANKS = {
    2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8',
    9: '9', 10: '10', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'
}

# Hand rank names
HAND_NAMES = {
    0: 'High Card',
    1: 'One Pair',
    2: 'Two Pair',
    3: 'Three of a Kind',
    4: 'Straight',
    5: 'Flush',
    6: 'Full House',
    7: 'Four of a Kind',
    8: 'Straight Flush',
    9: 'Royal Flush',
}

# UI dimensions
MIN_TERMINAL_WIDTH = 140    # Wider for multiplayer layout
MIN_TERMINAL_HEIGHT = 40    # Taller for 4-player table to avoid overlaps
BOARD_MARGIN_X = 2          # Horizontal margin from terminal edges
BOARD_HEIGHT_PERCENT = 0.75  # Board takes 75% of terminal height
LOG_LINES = 8               # Lines reserved for scrolling log

# Multiplayer configuration
MIN_PLAYERS = 2
MAX_PLAYERS = 4
