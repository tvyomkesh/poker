"""Main poker game logic for Texas Hold'em."""

from enum import Enum, auto
from typing import List, Optional, Tuple, Callable
from .cards import Card, Deck
from .hand_eval import HandEvaluator
from .player import Player, PlayerAction
from .constants import SMALL_BLIND, BIG_BLIND, MIN_PLAYERS, MAX_PLAYERS


class GamePhase(Enum):
    """Phases of a Texas Hold'em hand."""
    WAITING = auto()      # Waiting to start
    PRE_FLOP = auto()     # Initial betting round
    FLOP = auto()         # After 3 community cards
    TURN = auto()         # After 4th community card
    RIVER = auto()        # After 5th community card
    SHOWDOWN = auto()     # Hand complete, show cards
    GAME_OVER = auto()    # Someone is bust


class PokerGame:
    """Manages a Texas Hold'em poker game for 2-4 players."""

    def __init__(self, players: List[Player],
                 on_action: Optional[Callable] = None):
        """
        Initialize the poker game.

        Args:
            players: List of players (first is human, rest are bots)
            on_action: Callback for action logging
        """
        if len(players) < MIN_PLAYERS or len(players) > MAX_PLAYERS:
            raise ValueError(f"Game requires {MIN_PLAYERS}-{MAX_PLAYERS} players")
        self.players = players
        self.num_players = len(players)
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = BIG_BLIND
        self.phase = GamePhase.WAITING
        self.current_player_idx = 0
        self.dealer_idx = 0
        self.last_raiser_idx = -1
        self.actions_this_round = 0  # Track number of actions in current betting round
        self.on_action = on_action
        self.winner: Optional[Player] = None
        self.winning_description = ""
        self.hand_number = 0

    @property
    def current_player(self) -> Player:
        """Get the current player to act."""
        return self.players[self.current_player_idx]

    def get_opponents(self, player_idx: int = None) -> List[Player]:
        """Get all players except the specified player (defaults to current)."""
        if player_idx is None:
            player_idx = self.current_player_idx
        return [p for i, p in enumerate(self.players) if i != player_idx]

    def get_active_opponents(self, player_idx: int = None) -> List[Player]:
        """Get opponents who haven't folded."""
        return [p for p in self.get_opponents(player_idx) if not p.folded]

    @property
    def dealer(self) -> Player:
        """Get the dealer (button)."""
        return self.players[self.dealer_idx]

    def log_action(self, message: str):
        """Log an action if callback is set."""
        if self.on_action:
            self.on_action(message)

    def start_hand(self):
        """Start a new hand."""
        self.hand_number += 1

        # Reset game state
        self.deck.reset()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = BIG_BLIND
        self.winner = None
        self.winning_description = ""
        self.last_raiser_idx = -1

        # Reset players
        for player in self.players:
            player.reset_hand()

        # Set dealer button
        for i, player in enumerate(self.players):
            player.is_dealer = (i == self.dealer_idx)

        # Deal hole cards
        for player in self.players:
            player.receive_cards(self.deck.deal(2))

        # Post blinds
        if self.num_players == 2:
            # Heads-up special rule: dealer posts SB
            sb_idx = self.dealer_idx
            bb_idx = (self.dealer_idx + 1) % self.num_players
        else:
            # Multi-way: SB is left of dealer, BB is left of SB
            sb_idx = (self.dealer_idx + 1) % self.num_players
            bb_idx = (self.dealer_idx + 2) % self.num_players

        sb_player = self.players[sb_idx]
        bb_player = self.players[bb_idx]

        sb_amount = sb_player.bet(SMALL_BLIND)
        self.pot += sb_amount
        self.log_action(f"{sb_player.name} posts small blind ${SMALL_BLIND}")

        bb_amount = bb_player.bet(BIG_BLIND)
        self.pot += bb_amount
        self.current_bet = BIG_BLIND
        self.log_action(f"{bb_player.name} posts big blind ${BIG_BLIND}")

        # Pre-flop action starts left of BB
        if self.num_players == 2:
            # Heads-up: dealer (SB) acts first pre-flop
            self.current_player_idx = self.dealer_idx
        else:
            # Multi-way: player left of BB acts first (UTG)
            self.current_player_idx = (bb_idx + 1) % self.num_players

        self.phase = GamePhase.PRE_FLOP
        self.actions_this_round = 0

    def process_action(self, action: PlayerAction, amount: int = 0) -> bool:
        """
        Process a player action.

        Args:
            action: The action taken
            amount: Raise amount (if applicable)

        Returns:
            True if the hand continues, False if hand is over
        """
        player = self.current_player

        if action == PlayerAction.FOLD:
            player.folded = True
            player.last_action = "Folded"
            self.log_action(f"{player.name} folded")

            # Check if only one player remains
            active_players = [p for p in self.players if not p.folded]
            if len(active_players) == 1:
                self._end_hand_fold()
                return False
            # Otherwise continue with next player

        elif action == PlayerAction.CHECK:
            player.last_action = "Checked"
            self.log_action(f"{player.name} checked")

        elif action == PlayerAction.CALL:
            call_amount = player.amount_to_call(self.current_bet)
            actual = player.bet(call_amount)
            self.pot += actual
            if player.is_all_in:
                player.last_action = f"Called ${actual} (all-in)"
                self.log_action(f"{player.name} called ${actual} (all-in)")
            else:
                player.last_action = f"Called ${actual}"
                self.log_action(f"{player.name} called ${actual}")

        elif action == PlayerAction.RAISE:
            # First call the current bet
            call_amount = player.amount_to_call(self.current_bet)
            if call_amount > 0:
                player.bet(call_amount)
                self.pot += call_amount

            # Then raise
            raise_amount = min(amount, player.chips)
            actual = player.bet(raise_amount)
            self.pot += actual
            self.current_bet += actual
            self.min_raise = actual
            self.last_raiser_idx = self.current_player_idx

            if player.is_all_in:
                player.last_action = f"Raised to ${self.current_bet} (all-in)"
                self.log_action(f"{player.name} raised to ${self.current_bet} (all-in)")
            else:
                player.last_action = f"Raised to ${self.current_bet}"
                self.log_action(f"{player.name} raised to ${self.current_bet}")

        elif action == PlayerAction.ALL_IN:
            all_in_amount = player.chips
            actual = player.bet(all_in_amount)
            self.pot += actual

            if actual > self.current_bet - player.current_bet + actual:
                # It's a raise
                old_bet = self.current_bet
                self.current_bet = player.current_bet
                self.min_raise = self.current_bet - old_bet
                self.last_raiser_idx = self.current_player_idx
                player.last_action = f"All-in ${actual}"
                self.log_action(f"{player.name} went all-in for ${actual}")
            else:
                player.last_action = f"Called all-in ${actual}"
                self.log_action(f"{player.name} called all-in for ${actual}")

        # Track actions taken this round
        self.actions_this_round += 1

        # Check if betting round is complete
        if self._is_betting_complete():
            return self._advance_phase()

        # Move to next player
        self._next_player()
        return True

    def _is_betting_complete(self) -> bool:
        """Check if the current betting round is complete."""
        active_players = [p for p in self.players if p.can_act()]
        active_count = len(active_players)

        # If only one player can act, betting is done
        if active_count <= 1:
            return True

        # Each active player must have acted at least once this round
        if self.actions_this_round < active_count:
            return False

        # All active players must have matched the current bet
        for player in active_players:
            if player.current_bet < self.current_bet:
                return False

        # If someone raised, everyone else must have responded
        if self.last_raiser_idx != -1:
            # Betting complete when someone OTHER than the raiser just acted
            # and all bets are matched
            return self.current_player_idx != self.last_raiser_idx

        # No raises this round - everyone has acted and matched
        return True

    def _next_player(self):
        """Move to the next active player in rotation."""
        start_idx = self.current_player_idx

        for _ in range(self.num_players):
            self.current_player_idx = (self.current_player_idx + 1) % self.num_players
            if self.current_player.can_act():
                return

        # No player can act (all folded or all-in)
        self.current_player_idx = start_idx

    def _advance_phase(self) -> bool:
        """
        Advance to the next phase of the hand.

        Returns:
            True if hand continues, False if showdown/end
        """
        # Reset betting for new round
        for player in self.players:
            player.current_bet = 0
        self.current_bet = 0
        self.last_raiser_idx = -1
        self.actions_this_round = 0

        # Check if we should go straight to showdown
        active_count = sum(1 for p in self.players if not p.folded)
        can_act_count = sum(1 for p in self.players if p.can_act())

        if active_count == 1:
            # Someone folded
            return False

        if can_act_count == 0:
            # All remaining players are all-in - run out the board
            while self.phase != GamePhase.SHOWDOWN:
                self._deal_next_phase()
            self._showdown()
            return False

        # Deal next community cards
        self._deal_next_phase()

        if self.phase == GamePhase.SHOWDOWN:
            self._showdown()
            return False

        # Post-flop: first active player left of dealer acts first
        self.current_player_idx = self.dealer_idx
        self._next_player()  # Find first active player left of dealer

        return True

    def _deal_next_phase(self):
        """Deal community cards for the next phase."""
        if self.phase == GamePhase.PRE_FLOP:
            # Flop - burn one, deal three
            self.deck.burn()
            self.community_cards.extend(self.deck.deal(3))
            self.phase = GamePhase.FLOP
            self.log_action(f"*** FLOP *** {self._format_community()}")

        elif self.phase == GamePhase.FLOP:
            # Turn - burn one, deal one
            self.deck.burn()
            self.community_cards.extend(self.deck.deal(1))
            self.phase = GamePhase.TURN
            self.log_action(f"*** TURN *** {self._format_community()}")

        elif self.phase == GamePhase.TURN:
            # River - burn one, deal one
            self.deck.burn()
            self.community_cards.extend(self.deck.deal(1))
            self.phase = GamePhase.RIVER
            self.log_action(f"*** RIVER *** {self._format_community()}")

        elif self.phase == GamePhase.RIVER:
            self.phase = GamePhase.SHOWDOWN

    def _format_community(self) -> str:
        """Format community cards for logging."""
        return ' '.join(str(c) for c in self.community_cards)

    def _end_hand_fold(self):
        """End hand when all but one player has folded."""
        # Find the remaining player who hasn't folded
        active_players = [p for p in self.players if not p.folded]

        if len(active_players) == 1:
            winner = active_players[0]
            self.winner = winner
            winner.win_pot(self.pot)
            self.winning_description = "by fold"
            self.log_action(f"{winner.name} won ${self.pot}")
            self.phase = GamePhase.SHOWDOWN
            self._check_game_over()
        # If more than one player remains, continue the hand

    def _showdown(self):
        """Determine winner(s) at showdown - supports multi-way pots."""
        self.phase = GamePhase.SHOWDOWN

        # Get players still in the hand
        active_players = [p for p in self.players if not p.folded]

        if len(active_players) == 1:
            # Everyone else folded
            winner = active_players[0]
            self.winner = winner
            self.winning_description = "by fold"
            winner.win_pot(self.pot)
            self._check_game_over()
            return

        # Evaluate all hands
        hand_results = []
        for player in active_players:
            all_cards = player.hole_cards + self.community_cards
            rank, kickers, desc = HandEvaluator.evaluate_hand(all_cards)
            hand_results.append((player, rank, kickers, desc))

        # Sort by hand strength (best first)
        hand_results.sort(key=lambda x: (x[1], x[2]), reverse=True)

        # Find winner(s) - could be ties
        best_rank, best_kickers = hand_results[0][1], hand_results[0][2]
        winners = [(p, desc) for p, rank, kickers, desc in hand_results
                   if rank == best_rank and kickers == best_kickers]

        if len(winners) == 1:
            winner, desc = winners[0]
            self.winner = winner
            self.winning_description = desc
            winner.win_pot(self.pot)
            self.log_action(f"{winner.name} won ${self.pot} with {desc}")
        else:
            # Split pot among winners
            split_amount = self.pot // len(winners)
            remainder = self.pot % len(winners)

            for i, (winner, desc) in enumerate(winners):
                # Give remainder to first winner (arbitrary)
                amount = split_amount + (remainder if i == 0 else 0)
                winner.win_pot(amount)

            self.winner = None  # Tie
            self.winning_description = f"Split pot ({winners[0][1]})"
            winner_names = ', '.join(w[0].name for w in winners)
            self.log_action(f"Split pot! {winner_names} tie with {winners[0][1]}")

        self._check_game_over()

    def _check_game_over(self):
        """Check if the game is over (someone is bust)."""
        for player in self.players:
            if player.chips <= 0:
                self.phase = GamePhase.GAME_OVER

    def next_hand(self):
        """Prepare for the next hand."""
        # Rotate dealer clockwise
        self.dealer_idx = (self.dealer_idx + 1) % self.num_players
        self.start_hand()

    def reset_game(self):
        """Reset the entire game."""
        for player in self.players:
            player.reset_chips()
        self.dealer_idx = 0
        self.hand_number = 0
        self.phase = GamePhase.WAITING
        self.winner = None

    def get_game_state(self) -> dict:
        """Get current game state for bot decision making."""
        current = self.current_player
        opponents = self.get_active_opponents()

        # Determine position (simplified for multi-way)
        is_preflop = self.phase == GamePhase.PRE_FLOP
        if is_preflop:
            position = 'OOP' if current.is_dealer else 'IP'
        else:
            position = 'IP' if current.is_dealer else 'OOP'

        return {
            'community_cards': self.community_cards.copy(),
            'pot': self.pot,
            'current_bet': self.current_bet,
            'min_raise': self.min_raise,
            'phase': self.phase,
            'position': position,
            'num_opponents': len(opponents),
            'opponent_stacks': [p.chips for p in opponents],
            'opponent_bets': [p.current_bet for p in opponents],
            'opponent_stack': opponents[0].chips if opponents else 0,  # Backwards compat
            'stack_to_pot': current.chips / self.pot if self.pot > 0 else float('inf'),
        }

    def get_valid_actions(self) -> List[PlayerAction]:
        """Get valid actions for the current player."""
        player = self.current_player
        actions = []

        to_call = player.amount_to_call(self.current_bet)

        if to_call == 0:
            actions.append(PlayerAction.CHECK)
        else:
            actions.append(PlayerAction.CALL)

        # Can always fold (even if you can check, though unusual)
        actions.append(PlayerAction.FOLD)

        # Can raise if we have chips beyond calling
        if player.chips > to_call:
            actions.append(PlayerAction.RAISE)

        return actions
