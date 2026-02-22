"""Easy difficulty bot - loose passive fish.

Characteristics:
- Plays too many hands (loose)
- Rarely raises (passive)
- Doesn't consider position
- Predictable betting patterns
- Easy to exploit
"""

import random
from typing import Tuple
from .base import BotBase, BotDifficulty
from game.player import PlayerAction
from game.hand_eval import HandEvaluator
from game.constants import STARTING_CHIPS, BIG_BLIND


class EasyBot(BotBase):
    """A loose-passive bot that plays too many hands and rarely raises."""

    difficulty = BotDifficulty.EASY

    def __init__(self, name: str = "Fish", chips: int = STARTING_CHIPS):
        super().__init__(name, chips)
        # Easy bot has high randomness
        self.calling_threshold = 0.15  # Will call with very weak hands
        self.raise_threshold = 0.7     # Only raises with strong hands
        self.bluff_frequency = 0.05    # Rarely bluffs

    def get_action(self, game_state: dict) -> Tuple[PlayerAction, int]:
        """Make a decision - loose and passive."""
        community_cards = game_state.get('community_cards', [])
        pot = game_state.get('pot', 0)
        current_bet = game_state.get('current_bet', 0)
        min_raise = game_state.get('min_raise', BIG_BLIND)

        # Calculate basic hand strength
        strength = HandEvaluator.get_hand_strength(
            self.hole_cards, community_cards
        )

        # Add some randomness (fish are inconsistent)
        strength += random.uniform(-0.15, 0.15)

        to_call = self.amount_to_call(current_bet)

        # Decision logic - very simple
        if to_call == 0:
            # Can check - occasionally bet with decent hands
            if strength > self.raise_threshold or random.random() < self.bluff_frequency:
                raise_amount = self._calculate_bet(strength, pot, min_raise)
                return PlayerAction.RAISE, raise_amount
            return PlayerAction.CHECK, 0

        # Must call or fold
        # Fish call too much - especially against big "scary" bets (they don't believe you)
        raise_ratio = current_bet / pot if pot > 0 else 1
        is_big_raise = raise_ratio > 2.0

        # Fish are suspicious of big bets - "nobody bets that much with a real hand!"
        if is_big_raise:
            # Call more often against big bets
            if random.random() < 0.6 or strength > 0.25:
                return PlayerAction.CALL, 0

        if strength > self.calling_threshold or random.random() < 0.35:
            # Sometimes raise with good hands
            if strength > self.raise_threshold and self.chips > to_call:
                raise_amount = self._calculate_bet(strength, pot, min_raise)
                return PlayerAction.RAISE, raise_amount
            return PlayerAction.CALL, 0

        # Occasionally fold (even fish fold sometimes) - but not as often against big bets
        if to_call > pot * 0.5 and strength < 0.15 and not is_big_raise:
            return PlayerAction.FOLD, 0

        # Default: call (fish love to call)
        return PlayerAction.CALL, 0

    def _calculate_bet(self, strength: float, pot: int, min_raise: int) -> int:
        """Calculate bet size - fish bet randomly sized amounts."""
        # Fish don't size bets well
        if random.random() < 0.3:
            # Min bet
            return min_raise
        elif random.random() < 0.5:
            # Random pot fraction
            bet = int(pot * random.uniform(0.3, 1.0))
        else:
            # Random amount
            bet = int(self.chips * random.uniform(0.1, 0.3))

        return max(min_raise, min(bet, self.chips))
