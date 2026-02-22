"""Medium difficulty bot - tight aggressive regular.

Characteristics:
- Plays solid pre-flop ranges
- Position aware
- Aggressive with good hands
- Basic pot odds understanding
- Can be exploited by advanced players
"""

import random
from typing import Tuple
from .base import BotBase, BotDifficulty
from .ranges import (
    get_hand_notation, get_hand_tier, hand_in_range,
    PREMIUM_HANDS, STRONG_HANDS, PLAYABLE_HANDS,
    THREE_BET_RANGE, categorize_made_hand
)
from game.player import PlayerAction
from game.hand_eval import HandEvaluator
from game.constants import STARTING_CHIPS, BIG_BLIND
from game.poker import GamePhase


class MediumBot(BotBase):
    """A tight-aggressive bot that plays solid fundamental poker."""

    difficulty = BotDifficulty.MEDIUM

    def __init__(self, name: str = "Shark", chips: int = STARTING_CHIPS):
        super().__init__(name, chips)

    def get_action(self, game_state: dict) -> Tuple[PlayerAction, int]:
        """Make a decision using TAG strategy."""
        community_cards = game_state.get('community_cards', [])
        pot = game_state.get('pot', 0)
        current_bet = game_state.get('current_bet', 0)
        min_raise = game_state.get('min_raise', BIG_BLIND)
        phase = game_state.get('phase', GamePhase.PRE_FLOP)
        position = game_state.get('position', 'IP')

        to_call = self.amount_to_call(current_bet)

        if phase == GamePhase.PRE_FLOP:
            return self._preflop_action(pot, current_bet, min_raise, position, to_call)
        else:
            return self._postflop_action(
                community_cards, pot, current_bet, min_raise, position, to_call
            )

    def _preflop_action(self, pot: int, current_bet: int, min_raise: int,
                        position: str, to_call: int) -> Tuple[PlayerAction, int]:
        """Pre-flop decision using hand ranges."""
        hand_notation = get_hand_notation(self.hole_cards[0], self.hole_cards[1])
        tier = get_hand_tier(hand_notation)
        facing_raise = to_call > BIG_BLIND

        # Detect big raises (potential bluffs) - don't over-fold
        raise_ratio = current_bet / pot if pot > 0 else current_bet / BIG_BLIND
        is_big_raise = raise_ratio > 2.0

        # Premium hands - always raise/re-raise
        if tier == 1:
            raise_amount = self._size_raise(pot, min_raise, 3.0)
            return PlayerAction.RAISE, raise_amount

        # Strong hands
        if tier == 2:
            if facing_raise:
                # Big raises are suspicious - call or re-raise more often
                if is_big_raise or (hand_notation in THREE_BET_RANGE and random.random() < 0.5):
                    raise_amount = self._size_raise(pot, min_raise, 3.0)
                    return PlayerAction.RAISE, raise_amount
                return PlayerAction.CALL, 0
            else:
                raise_amount = self._size_raise(pot, min_raise, 2.5)
                return PlayerAction.RAISE, raise_amount

        # Playable hands
        if tier == 3:
            if facing_raise:
                # Against big raises, call more often (they might be bluffing)
                if is_big_raise:
                    if random.random() < 0.6:  # Call 60% of the time vs big raises
                        return PlayerAction.CALL, 0
                    return PlayerAction.FOLD, 0
                # Normal raise - call in position
                if position == 'IP' and to_call <= pot * 0.4:
                    return PlayerAction.CALL, 0
                if random.random() < 0.3:  # Defend 30% out of position too
                    return PlayerAction.CALL, 0
                return PlayerAction.FOLD, 0
            else:
                # Open raise
                raise_amount = self._size_raise(pot, min_raise, 2.5)
                return PlayerAction.RAISE, raise_amount

        # Speculative hands - defend against obvious bluffs
        if tier == 4:
            if not facing_raise:
                if position == 'IP' and random.random() < 0.5:
                    raise_amount = self._size_raise(pot, min_raise, 2.0)
                    return PlayerAction.RAISE, raise_amount
                if to_call == 0:
                    return PlayerAction.CHECK, 0
                return PlayerAction.FOLD, 0
            else:
                # Against big raises, call sometimes to not be exploited
                if is_big_raise and random.random() < 0.35:
                    return PlayerAction.CALL, 0
                if position == 'IP' and to_call <= pot * 0.25:
                    return PlayerAction.CALL, 0
                return PlayerAction.FOLD, 0

        # Trash hands - still defend occasionally against big bluffs
        if to_call == 0:
            return PlayerAction.CHECK, 0
        if is_big_raise and random.random() < 0.15:
            return PlayerAction.CALL, 0
        return PlayerAction.FOLD, 0

    def _postflop_action(self, community_cards: list, pot: int, current_bet: int,
                         min_raise: int, position: str,
                         to_call: int) -> Tuple[PlayerAction, int]:
        """Post-flop decision based on hand strength and position."""
        all_cards = self.hole_cards + community_cards
        rank, kickers, desc = HandEvaluator.evaluate_hand(all_cards)
        category = categorize_made_hand(rank)

        # Calculate pot odds
        pot_odds = to_call / (pot + to_call) if (pot + to_call) > 0 else 0

        # Monster hands - bet/raise for value
        if category == 'monster':
            if to_call == 0:
                bet = self._size_value_bet(pot, min_raise, 0.75)
                return PlayerAction.RAISE, bet
            else:
                raise_amount = self._size_raise(pot, min_raise, 2.5)
                return PlayerAction.RAISE, raise_amount

        # Strong hands - bet for value, call raises
        if category == 'strong':
            if to_call == 0:
                bet = self._size_value_bet(pot, min_raise, 0.66)
                return PlayerAction.RAISE, bet
            elif to_call <= pot * 0.5:
                return PlayerAction.CALL, 0
            else:
                # Big raise - just call
                return PlayerAction.CALL, 0

        # Medium hands - bet in position, check/call out of position
        if category == 'medium':
            if to_call == 0:
                if position == 'IP':
                    bet = self._size_value_bet(pot, min_raise, 0.5)
                    return PlayerAction.RAISE, bet
                return PlayerAction.CHECK, 0
            elif pot_odds < 0.25:
                return PlayerAction.CALL, 0
            else:
                return PlayerAction.FOLD, 0

        # Weak hands (one pair) - check/call small bets
        if category == 'weak':
            if to_call == 0:
                # Occasionally bet as a bluff
                if position == 'IP' and random.random() < 0.3:
                    bet = self._size_value_bet(pot, min_raise, 0.33)
                    return PlayerAction.RAISE, bet
                return PlayerAction.CHECK, 0
            elif pot_odds < 0.2:
                return PlayerAction.CALL, 0
            else:
                return PlayerAction.FOLD, 0

        # Nothing - bluff occasionally, otherwise give up
        if to_call == 0:
            # Bluff with some frequency in position
            if position == 'IP' and random.random() < 0.25:
                bet = self._size_value_bet(pot, min_raise, 0.5)
                return PlayerAction.RAISE, bet
            return PlayerAction.CHECK, 0

        return PlayerAction.FOLD, 0

    def _size_raise(self, pot: int, min_raise: int, multiplier: float) -> int:
        """Size a raise as a multiple of the pot."""
        raise_amount = int(pot * multiplier)
        raise_amount = max(raise_amount, min_raise)
        raise_amount = min(raise_amount, self.chips)
        return raise_amount

    def _size_value_bet(self, pot: int, min_raise: int, pot_fraction: float) -> int:
        """Size a bet as a fraction of the pot."""
        bet = int(pot * pot_fraction)
        bet = max(bet, min_raise)
        bet = min(bet, self.chips)
        return bet
