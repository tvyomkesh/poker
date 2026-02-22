"""Poker odds calculator using Monte Carlo simulation."""

import random
from typing import List, Dict, Tuple
from .cards import Card, Deck
from .hand_eval import HandEvaluator, HandRank


class OddsCalculator:
    """Calculates poker hand probabilities using Monte Carlo simulation."""

    # Number of simulations for probability estimation
    SIMULATIONS = 1000

    @classmethod
    def calculate_probabilities(cls, hole_cards: List[Card],
                                community_cards: List[Card]) -> Dict[str, float]:
        """
        Calculate probability of making each hand type.

        Args:
            hole_cards: Player's 2 hole cards
            community_cards: Current community cards (0-5)

        Returns:
            Dictionary mapping hand names to probabilities (0-100)
        """
        if len(hole_cards) != 2:
            return {}

        # If all 5 community cards are out, just evaluate the actual hand
        if len(community_cards) == 5:
            return cls._evaluate_final_hand(hole_cards, community_cards)

        # Cards already in play
        used_cards = set(hole_cards + community_cards)

        # Build remaining deck
        remaining_deck = []
        for suit in ['spades', 'hearts', 'diamonds', 'clubs']:
            for rank in range(2, 15):
                card = Card(rank, suit)
                if card not in used_cards:
                    remaining_deck.append(card)

        # Count outcomes
        hand_counts = {rank: 0 for rank in HandRank}
        cards_needed = 5 - len(community_cards)

        for _ in range(cls.SIMULATIONS):
            # Randomly complete the board
            sampled = random.sample(remaining_deck, cards_needed)
            full_community = community_cards + sampled
            all_cards = hole_cards + full_community

            # Evaluate hand
            rank, _, _ = HandEvaluator.evaluate_hand(all_cards)
            hand_counts[rank] += 1

        # Convert to probabilities
        probabilities = {}
        for rank in HandRank:
            prob = (hand_counts[rank] / cls.SIMULATIONS) * 100
            if prob > 0.1:  # Only show if > 0.1%
                probabilities[rank.name] = prob

        return probabilities

    @classmethod
    def _evaluate_final_hand(cls, hole_cards: List[Card],
                             community_cards: List[Card]) -> Dict[str, float]:
        """Evaluate the final hand when all cards are known."""
        all_cards = hole_cards + community_cards
        rank, _, _ = HandEvaluator.evaluate_hand(all_cards)

        # Return 100% for the actual hand
        return {rank.name: 100.0}

    @classmethod
    def calculate_win_probability(cls, hole_cards: List[Card],
                                  community_cards: List[Card],
                                  num_opponents: int = 1) -> float:
        """
        Estimate probability of winning against random opponent hands.

        Args:
            hole_cards: Player's 2 hole cards
            community_cards: Current community cards
            num_opponents: Number of opponents

        Returns:
            Win probability as percentage (0-100)
        """
        if len(hole_cards) != 2:
            return 0.0

        used_cards = set(hole_cards + community_cards)

        remaining_deck = []
        for suit in ['spades', 'hearts', 'diamonds', 'clubs']:
            for rank in range(2, 15):
                card = Card(rank, suit)
                if card not in used_cards:
                    remaining_deck.append(card)

        wins = 0
        ties = 0
        cards_needed = 5 - len(community_cards)

        for _ in range(cls.SIMULATIONS):
            deck_copy = remaining_deck.copy()
            random.shuffle(deck_copy)

            # Complete the board
            board_cards = deck_copy[:cards_needed]
            full_community = community_cards + board_cards
            deck_copy = deck_copy[cards_needed:]

            # Player's hand
            player_cards = hole_cards + full_community

            # Deal opponent hands and compare
            player_wins = True
            is_tie = False

            for _ in range(num_opponents):
                opp_hole = [deck_copy.pop(), deck_copy.pop()]
                opp_cards = opp_hole + full_community

                result = HandEvaluator.compare_hands(player_cards, opp_cards)
                if result < 0:
                    player_wins = False
                    break
                elif result == 0:
                    is_tie = True

            if player_wins and not is_tie:
                wins += 1
            elif is_tie:
                ties += 1

        # Win probability (ties count as half)
        return ((wins + ties * 0.5) / cls.SIMULATIONS) * 100

    @classmethod
    def get_outs(cls, hole_cards: List[Card],
                 community_cards: List[Card]) -> Dict[str, int]:
        """
        Calculate number of outs for improving hands.

        Returns:
            Dictionary with out counts for different draws
        """
        if len(hole_cards) != 2 or len(community_cards) < 3:
            return {}

        all_cards = hole_cards + community_cards
        current_rank, _, _ = HandEvaluator.evaluate_hand(all_cards)

        used_cards = set(all_cards)
        outs = {}

        # Check each remaining card
        flush_outs = 0
        straight_outs = 0
        pair_outs = 0

        for suit in ['spades', 'hearts', 'diamonds', 'clubs']:
            for rank in range(2, 15):
                card = Card(rank, suit)
                if card in used_cards:
                    continue

                # Test if this card improves our hand
                test_cards = all_cards + [card]
                new_rank, _, _ = HandEvaluator.evaluate_hand(test_cards)

                if new_rank > current_rank:
                    if new_rank == HandRank.FLUSH:
                        flush_outs += 1
                    elif new_rank == HandRank.STRAIGHT:
                        straight_outs += 1
                    elif new_rank in (HandRank.ONE_PAIR, HandRank.TWO_PAIR,
                                      HandRank.THREE_OF_A_KIND):
                        pair_outs += 1

        if flush_outs > 0:
            outs['Flush'] = flush_outs
        if straight_outs > 0:
            outs['Straight'] = straight_outs
        if pair_outs > 0:
            outs['Pair+'] = pair_outs

        return outs
