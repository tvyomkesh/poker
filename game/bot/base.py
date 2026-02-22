"""Base bot class and difficulty enum."""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any
from game.player import Player, PlayerAction
from game.constants import STARTING_CHIPS


class BotDifficulty(Enum):
    """Bot difficulty levels."""
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class BotBase(Player, ABC):
    """Abstract base class for all bot implementations."""

    difficulty: BotDifficulty = BotDifficulty.EASY

    def __init__(self, name: str, chips: int = STARTING_CHIPS):
        super().__init__(name, chips)
        self.is_human = False

        # Statistics for opponent modeling
        self.hands_played = 0
        self.vpip_hands = 0  # Voluntarily put money in pot
        self.pfr_hands = 0   # Pre-flop raise
        self.aggression_actions = 0  # Bets + raises
        self.passive_actions = 0     # Calls + checks

        # Opponent stats (for tracking human player)
        self.opponent_stats: Dict[str, Any] = {
            'vpip': 0.5,        # Voluntarily put $ in pot %
            'pfr': 0.3,         # Pre-flop raise %
            'aggression': 1.0,  # Aggression factor
            'hands_seen': 0,
        }

    @abstractmethod
    def get_action(self, game_state: dict) -> Tuple[PlayerAction, int]:
        """
        Determine the bot's action based on game state.

        Args:
            game_state: Dictionary containing:
                - community_cards: List of community cards
                - pot: Current pot size
                - current_bet: Current bet to call
                - min_raise: Minimum raise amount
                - phase: Current game phase
                - opponent_stack: Opponent's chip count
                - position: 'IP' (in position) or 'OOP' (out of position)

        Returns:
            Tuple of (action, raise_amount)
        """
        pass

    def update_opponent_stats(self, action: PlayerAction, is_preflop: bool,
                              had_to_call: bool):
        """Update opponent modeling statistics."""
        stats = self.opponent_stats
        stats['hands_seen'] += 1
        n = stats['hands_seen']

        # Update VPIP (called or raised when didn't have to)
        if had_to_call and action in (PlayerAction.CALL, PlayerAction.RAISE):
            new_vpip = (stats['vpip'] * (n - 1) + 1) / n
            stats['vpip'] = new_vpip

        # Update PFR
        if is_preflop and action == PlayerAction.RAISE:
            new_pfr = (stats['pfr'] * (n - 1) + 1) / n
            stats['pfr'] = new_pfr

        # Update aggression
        if action in (PlayerAction.RAISE,):
            self.aggression_actions += 1
        elif action in (PlayerAction.CALL, PlayerAction.CHECK):
            self.passive_actions += 1

        if self.passive_actions > 0:
            stats['aggression'] = self.aggression_actions / self.passive_actions

    def get_position(self, is_dealer: bool, is_preflop: bool) -> str:
        """Determine if bot is in position (IP) or out of position (OOP)."""
        # Pre-flop: dealer (button) acts first in heads-up, so OOP
        # Post-flop: non-dealer acts first, so dealer is IP
        if is_preflop:
            return 'OOP' if is_dealer else 'IP'
        else:
            return 'IP' if is_dealer else 'OOP'
