"""Hard difficulty bot - near-GTO with exploitation.

Characteristics:
- Balanced pre-flop ranges with mixed strategies
- Proper bet sizing (geometric, polarized)
- Opponent modeling and exploitation
- Position mastery
- Balanced bluffing frequencies
- Very difficult to beat
"""

import random
from typing import Tuple, Dict
from .base import BotBase, BotDifficulty
from .ranges import (
    get_hand_notation, get_hand_tier, hand_in_range,
    get_preflop_action_frequencies, categorize_made_hand,
    PREMIUM_HANDS, STRONG_HANDS, PLAYABLE_HANDS, SPECULATIVE_HANDS,
    THREE_BET_VALUE, THREE_BET_BLUFF, CALL_VS_3BET
)
from game.player import PlayerAction
from game.hand_eval import HandEvaluator, HandRank
from game.constants import STARTING_CHIPS, BIG_BLIND
from game.poker import GamePhase


class HardBot(BotBase):
    """A near-GTO bot that plays balanced poker and exploits weaknesses."""

    difficulty = BotDifficulty.HARD

    def __init__(self, name: str = "Pro", chips: int = STARTING_CHIPS):
        super().__init__(name, chips)
        self.streets_in_hand = 0
        self.hand_history = []  # Track actions this hand

    def reset_hand(self):
        """Reset hand-specific state."""
        super().reset_hand()
        self.streets_in_hand = 0
        self.hand_history = []

    def get_action(self, game_state: dict) -> Tuple[PlayerAction, int]:
        """Make a GTO-informed decision with exploitation adjustments."""
        community_cards = game_state.get('community_cards', [])
        pot = game_state.get('pot', 0)
        current_bet = game_state.get('current_bet', 0)
        min_raise = game_state.get('min_raise', BIG_BLIND)
        phase = game_state.get('phase', GamePhase.PRE_FLOP)
        position = game_state.get('position', 'IP')
        opponent_stack = game_state.get('opponent_stack', STARTING_CHIPS)

        to_call = self.amount_to_call(current_bet)
        stack_to_pot = self.chips / pot if pot > 0 else float('inf')

        if phase == GamePhase.PRE_FLOP:
            return self._preflop_action_gto(
                pot, current_bet, min_raise, position, to_call, opponent_stack
            )
        else:
            return self._postflop_action_gto(
                community_cards, pot, current_bet, min_raise,
                position, to_call, phase, stack_to_pot
            )

    def _preflop_action_gto(self, pot: int, current_bet: int, min_raise: int,
                             position: str, to_call: int,
                             opponent_stack: int) -> Tuple[PlayerAction, int]:
        """GTO pre-flop with mixed strategies, adjusted for bet sizing."""
        hand_notation = get_hand_notation(self.hole_cards[0], self.hole_cards[1])
        facing_raise = to_call > BIG_BLIND

        # Detect overbet/big raise - ratio of bet to pot
        raise_size_ratio = current_bet / pot if pot > 0 else current_bet / BIG_BLIND
        is_big_raise = raise_size_ratio > 2.0  # Raise bigger than 2x pot is suspicious

        # Get action frequencies for this hand
        frequencies = get_preflop_action_frequencies(
            hand_notation, position, facing_raise
        )

        # Adjust frequencies based on opponent tendencies
        frequencies = self._exploit_adjust_preflop(frequencies, facing_raise)

        # Adjust for big raises - don't over-fold to obvious bluffs
        if is_big_raise and facing_raise:
            frequencies = self._adjust_for_big_raise(frequencies, hand_notation, raise_size_ratio)

        # Make decision based on frequencies (mixed strategy)
        action = self._select_action_by_frequency(frequencies, to_call)

        if action == PlayerAction.RAISE:
            # GTO sizing: 2.5x for opens, 3x for 3-bets
            multiplier = 3.0 if facing_raise else 2.5
            raise_amount = self._geometric_raise(pot, min_raise, multiplier)
            return PlayerAction.RAISE, raise_amount
        elif action == PlayerAction.CALL:
            return PlayerAction.CALL, 0
        elif action == PlayerAction.CHECK and to_call == 0:
            return PlayerAction.CHECK, 0
        else:
            return PlayerAction.FOLD, 0

    def _adjust_for_big_raise(self, frequencies: dict, hand_notation: str,
                               raise_ratio: float) -> dict:
        """Adjust frequencies when facing a big raise - don't over-fold."""
        tier = get_hand_tier(hand_notation)

        # Big raises are often bluffs - need to call more to not be exploited
        # The bigger the raise, the more likely it's polarized (nuts or bluff)

        if tier <= 2:  # Premium and strong hands - never fold, call or raise more
            frequencies['fold'] = 0.0
            frequencies['call'] = 0.5
            frequencies['raise'] = 0.5
        elif tier == 3:  # Playable hands - reduce folding significantly
            frequencies['fold'] = max(0.1, frequencies.get('fold', 0) * 0.3)
            frequencies['call'] = 0.7
            frequencies['raise'] = 0.2
        elif tier == 4:  # Speculative hands - still defend sometimes
            frequencies['fold'] = max(0.4, frequencies.get('fold', 0) * 0.6)
            frequencies['call'] = 0.5
            frequencies['raise'] = 0.1
        # Tier 5 (trash) can still fold most of the time

        # Normalize
        total = sum(frequencies.values())
        if total > 0:
            frequencies = {k: v / total for k, v in frequencies.items()}

        return frequencies

    def _postflop_action_gto(self, community_cards: list, pot: int,
                              current_bet: int, min_raise: int, position: str,
                              to_call: int, phase: GamePhase,
                              stack_to_pot: float) -> Tuple[PlayerAction, int]:
        """GTO post-flop play with balanced ranges."""
        all_cards = self.hole_cards + community_cards
        rank, kickers, desc = HandEvaluator.evaluate_hand(all_cards)
        category = categorize_made_hand(rank)

        # Calculate equity and pot odds
        pot_odds = to_call / (pot + to_call) if (pot + to_call) > 0 else 0

        # Analyze board texture
        board_texture = self._analyze_board(community_cards)

        # Get GTO-ish action frequencies
        frequencies = self._get_postflop_frequencies(
            category, position, to_call > 0, board_texture, stack_to_pot
        )

        # Exploit adjustments
        frequencies = self._exploit_adjust_postflop(frequencies, pot_odds)

        action = self._select_action_by_frequency(frequencies, to_call)

        if action == PlayerAction.RAISE:
            bet_size = self._calculate_bet_size(
                category, pot, min_raise, board_texture, to_call > 0
            )
            return PlayerAction.RAISE, bet_size
        elif action == PlayerAction.CALL:
            return PlayerAction.CALL, 0
        elif action == PlayerAction.CHECK and to_call == 0:
            return PlayerAction.CHECK, 0
        else:
            return PlayerAction.FOLD, 0

    def _get_postflop_frequencies(self, category: str, position: str,
                                   facing_bet: bool, board_texture: dict,
                                   stack_to_pot: float) -> dict:
        """Get GTO-approximate action frequencies for post-flop."""
        # Base frequencies by hand category
        if category == 'monster':
            if facing_bet:
                return {'fold': 0.0, 'call': 0.3, 'raise': 0.7}
            return {'fold': 0.0, 'call': 0.0, 'raise': 1.0}

        elif category == 'strong':
            if facing_bet:
                return {'fold': 0.0, 'call': 0.6, 'raise': 0.4}
            if position == 'IP':
                return {'fold': 0.0, 'call': 0.0, 'raise': 0.85}
            return {'fold': 0.0, 'call': 0.3, 'raise': 0.7}

        elif category == 'medium':
            if facing_bet:
                return {'fold': 0.2, 'call': 0.7, 'raise': 0.1}
            if position == 'IP':
                return {'fold': 0.0, 'call': 0.3, 'raise': 0.7}
            return {'fold': 0.0, 'call': 0.5, 'raise': 0.5}

        elif category == 'weak':
            if facing_bet:
                return {'fold': 0.5, 'call': 0.45, 'raise': 0.05}
            if position == 'IP':
                # Bet sometimes as bluff
                return {'fold': 0.0, 'call': 0.6, 'raise': 0.4}
            return {'fold': 0.0, 'call': 0.8, 'raise': 0.2}

        else:  # nothing
            if facing_bet:
                # Need to defend some frequency
                if board_texture.get('draw_heavy', False):
                    return {'fold': 0.6, 'call': 0.3, 'raise': 0.1}
                return {'fold': 0.75, 'call': 0.2, 'raise': 0.05}
            if position == 'IP':
                # Balanced bluffing frequency
                return {'fold': 0.0, 'call': 0.65, 'raise': 0.35}
            return {'fold': 0.0, 'call': 0.8, 'raise': 0.2}

    def _analyze_board(self, community_cards: list) -> dict:
        """Analyze board texture for strategic decisions."""
        if not community_cards:
            return {}

        suits = [c.suit for c in community_cards]
        ranks = sorted([c.rank for c in community_cards])

        texture = {
            'paired': len(ranks) != len(set(ranks)),
            'monotone': len(set(suits)) == 1,
            'two_tone': len(set(suits)) == 2,
            'connected': self._is_connected(ranks),
            'high': max(ranks) >= 12,  # Q or higher
            'draw_heavy': False,
        }

        # Check for draw-heavy boards
        if len(community_cards) >= 3:
            # Flush draw possible
            suit_counts = {}
            for s in suits:
                suit_counts[s] = suit_counts.get(s, 0) + 1
            if max(suit_counts.values()) >= 2:
                texture['draw_heavy'] = True

            # Straight draw possible
            if texture['connected']:
                texture['draw_heavy'] = True

        return texture

    def _is_connected(self, ranks: list) -> bool:
        """Check if ranks are connected (straight possible)."""
        if len(ranks) < 3:
            return False
        sorted_ranks = sorted(set(ranks))
        for i in range(len(sorted_ranks) - 1):
            if sorted_ranks[i + 1] - sorted_ranks[i] <= 2:
                return True
        return False

    def _select_action_by_frequency(self, frequencies: dict,
                                     to_call: int) -> PlayerAction:
        """Select action based on mixed strategy frequencies."""
        rand = random.random()
        cumulative = 0

        fold_freq = frequencies.get('fold', 0)
        call_freq = frequencies.get('call', 0)
        raise_freq = frequencies.get('raise', 0)

        cumulative += fold_freq
        if rand < cumulative:
            return PlayerAction.FOLD

        cumulative += call_freq
        if rand < cumulative:
            if to_call == 0:
                return PlayerAction.CHECK
            return PlayerAction.CALL

        return PlayerAction.RAISE

    def _exploit_adjust_preflop(self, frequencies: dict,
                                 facing_raise: bool) -> dict:
        """Adjust frequencies to exploit opponent tendencies."""
        stats = self.opponent_stats

        if stats['hands_seen'] < 10:
            return frequencies  # Not enough data

        # If opponent is too loose (high VPIP), tighten up value range
        if stats['vpip'] > 0.6:
            # They call too much - bet more for value, bluff less
            frequencies['raise'] = frequencies.get('raise', 0) * 1.2
            frequencies['fold'] = frequencies.get('fold', 0) * 0.8

        # If opponent is too tight, bluff more
        if stats['vpip'] < 0.3:
            frequencies['raise'] = frequencies.get('raise', 0) * 1.3

        # If opponent is passive, bet more aggressively
        if stats['aggression'] < 0.5:
            frequencies['raise'] = frequencies.get('raise', 0) * 1.2
            frequencies['call'] = frequencies.get('call', 0) * 0.8

        # Normalize
        total = sum(frequencies.values())
        if total > 0:
            frequencies = {k: v / total for k, v in frequencies.items()}

        return frequencies

    def _exploit_adjust_postflop(self, frequencies: dict,
                                  pot_odds: float) -> dict:
        """Adjust post-flop play based on opponent tendencies."""
        stats = self.opponent_stats

        if stats['hands_seen'] < 10:
            return frequencies

        # Against passive opponents, bet thinner for value
        if stats['aggression'] < 0.5:
            frequencies['raise'] = frequencies.get('raise', 0) * 1.3
            frequencies['call'] = frequencies.get('call', 0) * 0.7

        # Against aggressive opponents, trap more
        if stats['aggression'] > 2.0:
            frequencies['call'] = frequencies.get('call', 0) * 1.3
            frequencies['raise'] = frequencies.get('raise', 0) * 0.8

        # Normalize
        total = sum(frequencies.values())
        if total > 0:
            frequencies = {k: v / total for k, v in frequencies.items()}

        return frequencies

    def _geometric_raise(self, pot: int, min_raise: int,
                          multiplier: float) -> int:
        """Calculate a geometrically-sized raise."""
        raise_amount = int(pot * multiplier)
        raise_amount = max(raise_amount, min_raise)
        raise_amount = min(raise_amount, self.chips)
        return raise_amount

    def _calculate_bet_size(self, category: str, pot: int, min_raise: int,
                            board_texture: dict, facing_bet: bool) -> int:
        """Calculate optimal bet size based on range and board."""
        if facing_bet:
            # Raising - use 2.5-3x
            return self._geometric_raise(pot, min_raise, 2.75)

        # Betting - size based on board texture and hand
        if board_texture.get('draw_heavy', False):
            # Larger bets on draw-heavy boards
            fraction = 0.75
        elif category in ('monster', 'strong'):
            # Polarized sizing with strong hands
            fraction = 0.66
        else:
            # Smaller bets with bluffs and medium hands
            fraction = 0.33

        bet = int(pot * fraction)
        bet = max(bet, min_raise)
        bet = min(bet, self.chips)
        return bet
