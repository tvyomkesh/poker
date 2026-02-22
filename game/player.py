"""Player classes for Texas Hold'em Poker."""

import random
from typing import List, Optional, Tuple
from enum import Enum
from .cards import Card
from .hand_eval import HandEvaluator
from .constants import STARTING_CHIPS, BIG_BLIND


class PlayerAction(Enum):
    """Possible player actions."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


class Player:
    """Base class for a poker player."""

    def __init__(self, name: str, chips: int = STARTING_CHIPS):
        """
        Initialize a player.

        Args:
            name: Player's display name
            chips: Starting chip count
        """
        self.name = name
        self.chips = chips
        self.initial_chips = chips
        self.hole_cards: List[Card] = []
        self.current_bet = 0
        self.folded = False
        self.is_all_in = False
        self.is_dealer = False
        self.last_action: Optional[str] = None  # Track last action for display

    def reset_hand(self):
        """Reset player state for a new hand."""
        self.hole_cards = []
        self.current_bet = 0
        self.folded = False
        self.is_all_in = False
        self.last_action = None

    def reset_chips(self):
        """Reset chips to initial amount."""
        self.chips = self.initial_chips
        self.reset_hand()

    def receive_cards(self, cards: List[Card]):
        """Receive hole cards."""
        self.hole_cards = cards

    def bet(self, amount: int) -> int:
        """
        Place a bet.

        Args:
            amount: Amount to bet

        Returns:
            Actual amount bet (may be less if all-in)
        """
        actual_bet = min(amount, self.chips)
        self.chips -= actual_bet
        self.current_bet += actual_bet

        if self.chips == 0:
            self.is_all_in = True

        return actual_bet

    def win_pot(self, amount: int):
        """Add winnings to chip stack."""
        self.chips += amount

    def can_act(self) -> bool:
        """Check if player can still act (not folded or all-in)."""
        return not self.folded and not self.is_all_in

    def amount_to_call(self, current_bet: int) -> int:
        """Calculate amount needed to call."""
        return min(current_bet - self.current_bet, self.chips)

    def __str__(self) -> str:
        return f"{self.name} (${self.chips})"


class HumanPlayer(Player):
    """Human player controlled via keyboard input."""

    def __init__(self, name: str = "You", chips: int = STARTING_CHIPS):
        super().__init__(name, chips)
        self.is_human = True

    def get_action(self, game_state: dict) -> Tuple[PlayerAction, int]:
        """
        Human player action is determined by UI input.
        This method is a placeholder - actual input is handled by the display.

        Returns:
            Tuple of (action, amount for raises)
        """
        # This will be handled by the UI
        pass


class BotPlayer(Player):
    """AI-controlled player with basic poker strategy."""

    def __init__(self, name: str = "Bot", chips: int = STARTING_CHIPS):
        super().__init__(name, chips)
        self.is_human = False
        self.aggression = random.uniform(0.3, 0.7)  # Randomize personality

    def get_action(self, game_state: dict) -> Tuple[PlayerAction, int]:
        """
        Determine the bot's action based on hand strength and game state.

        Args:
            game_state: Dictionary containing:
                - community_cards: List of community cards
                - pot: Current pot size
                - current_bet: Current bet to call
                - min_raise: Minimum raise amount
                - phase: Current game phase

        Returns:
            Tuple of (action, raise_amount)
        """
        community_cards = game_state.get('community_cards', [])
        pot = game_state.get('pot', 0)
        current_bet = game_state.get('current_bet', 0)
        min_raise = game_state.get('min_raise', BIG_BLIND)

        # Calculate hand strength
        strength = HandEvaluator.get_hand_strength(self.hole_cards, community_cards)

        # Calculate pot odds
        to_call = self.amount_to_call(current_bet)
        pot_odds = to_call / (pot + to_call) if (pot + to_call) > 0 else 0

        # Add some randomness
        random_factor = random.uniform(-0.1, 0.1)
        effective_strength = strength + random_factor

        # Decision logic
        if to_call == 0:
            # Can check
            if effective_strength > 0.6 and random.random() < self.aggression:
                # Strong hand - raise
                raise_amount = self._calculate_raise(strength, pot, min_raise)
                return PlayerAction.RAISE, raise_amount
            else:
                return PlayerAction.CHECK, 0

        # Need to call or raise
        if effective_strength < 0.2 and to_call > pot * 0.3:
            # Weak hand, big bet - fold
            return PlayerAction.FOLD, 0

        if effective_strength > 0.7:
            # Strong hand
            if random.random() < self.aggression:
                # Raise
                raise_amount = self._calculate_raise(strength, pot, min_raise)
                return PlayerAction.RAISE, raise_amount
            else:
                return PlayerAction.CALL, 0

        if effective_strength > 0.4 or to_call <= pot_odds * pot:
            # Decent hand or good pot odds - call
            return PlayerAction.CALL, 0

        # Marginal hand, sometimes bluff
        if random.random() < 0.15:
            return PlayerAction.CALL, 0

        return PlayerAction.FOLD, 0

    def _calculate_raise(self, strength: float, pot: int, min_raise: int) -> int:
        """Calculate raise amount based on hand strength."""
        # Stronger hands get bigger raises
        multiplier = 1 + (strength * 2 * self.aggression)
        raise_amount = int(pot * multiplier * random.uniform(0.3, 0.7))

        # Ensure minimum raise
        raise_amount = max(raise_amount, min_raise)

        # Don't raise more than we have
        raise_amount = min(raise_amount, self.chips)

        return raise_amount
