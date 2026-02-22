"""Pre-flop hand ranges for poker strategy.

Hand notation:
- 'AA', 'KK' = pocket pairs
- 'AKs' = suited (same suit)
- 'AKo' = offsuit (different suits)
- 'A5s+' = A5s and better (A6s, A7s, etc.)

Ranges are defined as sets of hands that should be played in certain situations.
"""

from typing import Set, List, Tuple
from game.cards import Card


def get_hand_notation(card1: Card, card2: Card) -> str:
    """Convert two cards to standard hand notation."""
    r1, r2 = card1.rank, card2.rank
    suited = card1.suit == card2.suit

    # Ensure higher rank is first
    if r1 < r2:
        r1, r2 = r2, r1

    rank_chars = {14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T',
                  9: '9', 8: '8', 7: '7', 6: '6', 5: '5',
                  4: '4', 3: '3', 2: '2'}

    r1_char = rank_chars[r1]
    r2_char = rank_chars[r2]

    if r1 == r2:
        return f"{r1_char}{r2_char}"  # Pocket pair
    elif suited:
        return f"{r1_char}{r2_char}s"
    else:
        return f"{r1_char}{r2_char}o"


# =============================================================================
# PREMIUM HANDS (Top 5% - Always raise)
# =============================================================================
PREMIUM_HANDS = {
    'AA', 'KK', 'QQ', 'JJ', 'TT',
    'AKs', 'AKo', 'AQs', 'AQo',
}

# =============================================================================
# STRONG HANDS (Top 15% - Raise or call raises)
# =============================================================================
STRONG_HANDS = PREMIUM_HANDS | {
    '99', '88', '77',
    'AJs', 'AJo', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s',
    'KQs', 'KQo', 'KJs', 'KTs',
    'QJs', 'QTs',
    'JTs',
}

# =============================================================================
# PLAYABLE HANDS (Top 30% - Open raise, sometimes call)
# =============================================================================
PLAYABLE_HANDS = STRONG_HANDS | {
    '66', '55', '44', '33', '22',
    'A4s', 'A3s', 'A2s', 'ATo', 'A9o',
    'K9s', 'K8s', 'K7s', 'KJo', 'KTo',
    'Q9s', 'Q8s', 'QJo', 'QTo',
    'J9s', 'J8s', 'JTo',
    'T9s', 'T8s',
    '98s', '97s',
    '87s', '86s',
    '76s', '75s',
    '65s',
    '54s',
}

# =============================================================================
# SPECULATIVE HANDS (Top 50% - Play in position, with implied odds)
# =============================================================================
SPECULATIVE_HANDS = PLAYABLE_HANDS | {
    'A8o', 'A7o', 'A6o', 'A5o', 'A4o', 'A3o', 'A2o',
    'K6s', 'K5s', 'K4s', 'K3s', 'K2s', 'K9o', 'K8o',
    'Q7s', 'Q6s', 'Q5s', 'Q9o', 'Q8o',
    'J7s', 'J9o', 'J8o',
    'T7s', 'T6s', 'T9o', 'T8o',
    '96s', '95s', '98o', '97o',
    '85s', '84s', '87o', '86o',
    '74s', '73s', '76o', '75o',
    '64s', '63s', '65o',
    '53s', '54o',
    '43s',
}

# =============================================================================
# 3-BET RANGE (Hands to re-raise with)
# =============================================================================
THREE_BET_VALUE = {
    'AA', 'KK', 'QQ', 'JJ', 'TT',
    'AKs', 'AKo', 'AQs', 'AQo', 'AJs',
    'KQs',
}

THREE_BET_BLUFF = {
    'A5s', 'A4s', 'A3s', 'A2s',  # Suited aces (blockers + playability)
    'K5s', 'K4s',                  # Suited kings (blockers)
    '76s', '65s', '54s',           # Suited connectors
}

THREE_BET_RANGE = THREE_BET_VALUE | THREE_BET_BLUFF

# =============================================================================
# CALLING RANGE VS 3-BET
# =============================================================================
CALL_VS_3BET = {
    '99', '88', '77', '66',
    'AJs', 'ATs', 'A9s', 'A8s',
    'KQs', 'KJs', 'KTs',
    'QJs', 'QTs',
    'JTs',
    'T9s',
    '98s',
    '87s',
}

# =============================================================================
# ALL-IN RANGE (Short stack or facing all-in)
# =============================================================================
CALL_ALLIN = {
    'AA', 'KK', 'QQ', 'JJ', 'TT', '99',
    'AKs', 'AKo', 'AQs', 'AQo', 'AJs', 'AJo', 'ATs',
    'KQs', 'KQo',
}

PUSH_ALLIN = {
    'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77',
    'AKs', 'AKo', 'AQs', 'AQo', 'AJs', 'AJo', 'ATs', 'ATo', 'A9s', 'A8s',
    'KQs', 'KQo', 'KJs', 'KTs',
    'QJs',
}


# =============================================================================
# HAND STRENGTH TIERS
# =============================================================================
def get_hand_tier(hand_notation: str) -> int:
    """
    Get the tier (1-5) of a hand.
    1 = Premium, 5 = Trash

    Returns:
        Tier number (1-5)
    """
    if hand_notation in PREMIUM_HANDS:
        return 1
    elif hand_notation in STRONG_HANDS:
        return 2
    elif hand_notation in PLAYABLE_HANDS:
        return 3
    elif hand_notation in SPECULATIVE_HANDS:
        return 4
    else:
        return 5


def hand_in_range(card1: Card, card2: Card, range_set: Set[str]) -> bool:
    """Check if a hand is in the given range."""
    notation = get_hand_notation(card1, card2)
    return notation in range_set


def get_preflop_action_frequencies(hand_notation: str, position: str,
                                    facing_raise: bool) -> dict:
    """
    Get GTO-approximate action frequencies for a hand.

    Returns dict with frequencies (0-1) for: fold, call, raise
    These frequencies allow for mixed strategies (sometimes call, sometimes raise).
    """
    tier = get_hand_tier(hand_notation)

    if not facing_raise:
        # Opening action (no raise yet)
        if tier == 1:
            return {'fold': 0.0, 'call': 0.0, 'raise': 1.0}
        elif tier == 2:
            return {'fold': 0.0, 'call': 0.1, 'raise': 0.9}
        elif tier == 3:
            if position == 'IP':
                return {'fold': 0.1, 'call': 0.2, 'raise': 0.7}
            else:
                return {'fold': 0.3, 'call': 0.2, 'raise': 0.5}
        elif tier == 4:
            if position == 'IP':
                return {'fold': 0.4, 'call': 0.3, 'raise': 0.3}
            else:
                return {'fold': 0.7, 'call': 0.2, 'raise': 0.1}
        else:
            return {'fold': 0.9, 'call': 0.1, 'raise': 0.0}

    else:
        # Facing a raise
        if hand_notation in THREE_BET_VALUE:
            return {'fold': 0.0, 'call': 0.3, 'raise': 0.7}
        elif hand_notation in THREE_BET_BLUFF:
            return {'fold': 0.4, 'call': 0.2, 'raise': 0.4}
        elif hand_notation in CALL_VS_3BET:
            return {'fold': 0.2, 'call': 0.7, 'raise': 0.1}
        elif tier <= 3:
            return {'fold': 0.4, 'call': 0.5, 'raise': 0.1}
        elif tier == 4:
            return {'fold': 0.7, 'call': 0.3, 'raise': 0.0}
        else:
            return {'fold': 0.95, 'call': 0.05, 'raise': 0.0}


# =============================================================================
# POST-FLOP HAND CATEGORIES
# =============================================================================
def categorize_made_hand(hand_rank: int) -> str:
    """
    Categorize made hand strength for post-flop play.

    Args:
        hand_rank: HandRank enum value (0-9)

    Returns:
        Category: 'monster', 'strong', 'medium', 'weak', 'nothing'
    """
    if hand_rank >= 6:  # Full house or better
        return 'monster'
    elif hand_rank >= 4:  # Straight or flush
        return 'strong'
    elif hand_rank >= 2:  # Two pair or three of a kind
        return 'medium'
    elif hand_rank == 1:  # One pair
        return 'weak'
    else:
        return 'nothing'
