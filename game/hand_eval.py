"""Hand evaluation for Texas Hold'em Poker."""

from enum import IntEnum
from itertools import combinations
from typing import List, Tuple, Optional
from .cards import Card
from .constants import HAND_NAMES


class HandRank(IntEnum):
    """Poker hand rankings from lowest to highest."""
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9


class HandEvaluator:
    """Evaluates poker hands and determines winners."""

    @staticmethod
    def evaluate_hand(cards: List[Card]) -> Tuple[HandRank, List[int], str]:
        """
        Evaluate the best 5-card hand from the given cards.

        Args:
            cards: List of 5-7 cards (hole cards + community cards)

        Returns:
            Tuple of (HandRank, kicker values for tiebreaking, hand description)
        """
        if len(cards) < 5:
            raise ValueError("Need at least 5 cards to evaluate a hand")

        best_rank = HandRank.HIGH_CARD
        best_kickers: List[int] = []
        best_hand: List[Card] = []

        # Try all 5-card combinations
        for combo in combinations(cards, 5):
            hand = list(combo)
            rank, kickers = HandEvaluator._evaluate_five_cards(hand)

            # Compare: higher rank wins, then kickers
            if rank > best_rank or (rank == best_rank and kickers > best_kickers):
                best_rank = rank
                best_kickers = kickers
                best_hand = hand

        description = HandEvaluator._describe_hand(best_rank, best_hand)
        return best_rank, best_kickers, description

    @staticmethod
    def _evaluate_five_cards(cards: List[Card]) -> Tuple[HandRank, List[int]]:
        """Evaluate exactly 5 cards and return rank with kickers."""
        ranks = sorted([c.rank for c in cards], reverse=True)
        suits = [c.suit for c in cards]

        is_flush = len(set(suits)) == 1
        is_straight, straight_high = HandEvaluator._is_straight(ranks)

        # Count rank occurrences
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1

        counts = sorted(rank_counts.values(), reverse=True)
        # Sort ranks by count, then by rank value
        sorted_ranks = sorted(rank_counts.keys(),
                              key=lambda r: (rank_counts[r], r), reverse=True)

        # Royal Flush
        if is_flush and is_straight and straight_high == 14:
            return HandRank.ROYAL_FLUSH, [14]

        # Straight Flush
        if is_flush and is_straight:
            return HandRank.STRAIGHT_FLUSH, [straight_high]

        # Four of a Kind
        if counts == [4, 1]:
            return HandRank.FOUR_OF_A_KIND, sorted_ranks

        # Full House
        if counts == [3, 2]:
            return HandRank.FULL_HOUSE, sorted_ranks

        # Flush
        if is_flush:
            return HandRank.FLUSH, ranks

        # Straight
        if is_straight:
            return HandRank.STRAIGHT, [straight_high]

        # Three of a Kind
        if counts == [3, 1, 1]:
            return HandRank.THREE_OF_A_KIND, sorted_ranks

        # Two Pair
        if counts == [2, 2, 1]:
            return HandRank.TWO_PAIR, sorted_ranks

        # One Pair
        if counts == [2, 1, 1, 1]:
            return HandRank.ONE_PAIR, sorted_ranks

        # High Card
        return HandRank.HIGH_CARD, ranks

    @staticmethod
    def _is_straight(ranks: List[int]) -> Tuple[bool, int]:
        """
        Check if sorted ranks form a straight.

        Args:
            ranks: Sorted list of ranks (high to low)

        Returns:
            Tuple of (is_straight, high_card)
        """
        unique_ranks = sorted(set(ranks), reverse=True)
        if len(unique_ranks) != 5:
            return False, 0

        # Regular straight
        if unique_ranks[0] - unique_ranks[4] == 4:
            return True, unique_ranks[0]

        # Wheel (A-2-3-4-5)
        if unique_ranks == [14, 5, 4, 3, 2]:
            return True, 5  # 5-high straight

        return False, 0

    @staticmethod
    def _describe_hand(rank: HandRank, cards: List[Card]) -> str:
        """Generate a description of the hand."""
        ranks = sorted([c.rank for c in cards], reverse=True)
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1

        from .constants import RANKS

        if rank == HandRank.ROYAL_FLUSH:
            return "Royal Flush"
        elif rank == HandRank.STRAIGHT_FLUSH:
            high = max(ranks)
            return f"Straight Flush, {RANKS[high]} high"
        elif rank == HandRank.FOUR_OF_A_KIND:
            quad = [r for r, c in rank_counts.items() if c == 4][0]
            return f"Four of a Kind, {RANKS[quad]}s"
        elif rank == HandRank.FULL_HOUSE:
            trips = [r for r, c in rank_counts.items() if c == 3][0]
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            return f"Full House, {RANKS[trips]}s full of {RANKS[pair]}s"
        elif rank == HandRank.FLUSH:
            high = max(ranks)
            return f"Flush, {RANKS[high]} high"
        elif rank == HandRank.STRAIGHT:
            # Handle wheel
            if set(ranks) == {14, 2, 3, 4, 5}:
                return "Straight, 5 high"
            high = max(ranks)
            return f"Straight, {RANKS[high]} high"
        elif rank == HandRank.THREE_OF_A_KIND:
            trips = [r for r, c in rank_counts.items() if c == 3][0]
            return f"Three of a Kind, {RANKS[trips]}s"
        elif rank == HandRank.TWO_PAIR:
            pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
            return f"Two Pair, {RANKS[pairs[0]]}s and {RANKS[pairs[1]]}s"
        elif rank == HandRank.ONE_PAIR:
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            return f"Pair of {RANKS[pair]}s"
        else:
            high = max(ranks)
            return f"High Card, {RANKS[high]}"

    @staticmethod
    def compare_hands(hand1: List[Card], hand2: List[Card]) -> int:
        """
        Compare two hands.

        Returns:
            1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        rank1, kickers1, _ = HandEvaluator.evaluate_hand(hand1)
        rank2, kickers2, _ = HandEvaluator.evaluate_hand(hand2)

        if rank1 > rank2:
            return 1
        elif rank1 < rank2:
            return -1
        elif kickers1 > kickers2:
            return 1
        elif kickers1 < kickers2:
            return -1
        return 0

    @staticmethod
    def get_hand_strength(hole_cards: List[Card], community_cards: List[Card]) -> float:
        """
        Calculate a simple hand strength score (0.0 to 1.0).
        Used by the bot for decision making.

        Args:
            hole_cards: Player's 2 hole cards
            community_cards: Community cards (0-5)

        Returns:
            Strength score from 0.0 (worst) to 1.0 (best)
        """
        if not community_cards:
            # Pre-flop: evaluate starting hand strength
            return HandEvaluator._preflop_strength(hole_cards)

        all_cards = hole_cards + community_cards
        if len(all_cards) < 5:
            return HandEvaluator._preflop_strength(hole_cards)

        rank, kickers, _ = HandEvaluator.evaluate_hand(all_cards)

        # Base strength from hand rank
        base_strength = rank / 9.0  # Normalize to 0-1

        # Add kicker contribution
        kicker_bonus = 0
        if kickers:
            kicker_bonus = (kickers[0] - 2) / 12.0 * 0.1  # Small bonus for high kickers

        return min(1.0, base_strength + kicker_bonus)

    @staticmethod
    def _preflop_strength(hole_cards: List[Card]) -> float:
        """Calculate pre-flop hand strength."""
        if len(hole_cards) != 2:
            return 0.0

        c1, c2 = hole_cards
        r1, r2 = c1.rank, c2.rank
        high, low = max(r1, r2), min(r1, r2)
        suited = c1.suit == c2.suit

        # Pocket pairs
        if r1 == r2:
            # AA = 0.85, 22 = 0.35
            return 0.35 + (r1 - 2) * 0.04

        # Suited connectors and high cards
        gap = high - low
        base = (high + low - 4) / 24.0  # Base from card values

        # Suited bonus
        if suited:
            base += 0.05

        # Connector bonus
        if gap == 1:
            base += 0.03
        elif gap == 2:
            base += 0.01

        # Ace bonus
        if high == 14:
            base += 0.08

        return min(0.7, max(0.1, base))
