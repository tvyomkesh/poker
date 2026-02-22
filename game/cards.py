"""Card and Deck classes for Texas Hold'em Poker."""

import random
from typing import List, Optional
from .constants import SUITS, RANKS


class Card:
    """Represents a playing card."""

    SUIT_ORDER = ['clubs', 'diamonds', 'hearts', 'spades']

    def __init__(self, rank: int, suit: str):
        """
        Initialize a card.

        Args:
            rank: Card rank (2-14, where 11=J, 12=Q, 13=K, 14=A)
            suit: Card suit ('spades', 'hearts', 'diamonds', 'clubs')
        """
        if rank < 2 or rank > 14:
            raise ValueError(f"Invalid rank: {rank}")
        if suit not in SUITS:
            raise ValueError(f"Invalid suit: {suit}")

        self.rank = rank
        self.suit = suit

    @property
    def rank_str(self) -> str:
        """Get the string representation of the rank."""
        return RANKS[self.rank]

    @property
    def suit_symbol(self) -> str:
        """Get the Unicode symbol for the suit."""
        return SUITS[self.suit]

    @property
    def is_red(self) -> bool:
        """Check if the card is red (hearts or diamonds)."""
        return self.suit in ('hearts', 'diamonds')

    def __str__(self) -> str:
        """String representation of the card."""
        return f"{self.rank_str}{self.suit_symbol}"

    def __repr__(self) -> str:
        """Detailed representation of the card."""
        return f"Card({self.rank_str}, {self.suit})"

    def __eq__(self, other) -> bool:
        """Check equality with another card."""
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit

    def __lt__(self, other) -> bool:
        """Compare cards by rank, then suit."""
        if not isinstance(other, Card):
            return NotImplemented
        if self.rank != other.rank:
            return self.rank < other.rank
        return self.SUIT_ORDER.index(self.suit) < self.SUIT_ORDER.index(other.suit)

    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash((self.rank, self.suit))


class Deck:
    """Represents a standard 52-card deck."""

    def __init__(self):
        """Initialize a new shuffled deck."""
        self.cards: List[Card] = []
        self.reset()

    def reset(self):
        """Reset the deck with all 52 cards and shuffle."""
        self.cards = []
        for suit in SUITS.keys():
            for rank in range(2, 15):
                self.cards.append(Card(rank, suit))
        self.shuffle()

    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)

    def deal(self, count: int = 1) -> List[Card]:
        """
        Deal cards from the top of the deck.

        Args:
            count: Number of cards to deal

        Returns:
            List of dealt cards
        """
        if count > len(self.cards):
            raise ValueError(f"Cannot deal {count} cards, only {len(self.cards)} remaining")

        dealt = self.cards[:count]
        self.cards = self.cards[count:]
        return dealt

    def deal_one(self) -> Card:
        """Deal a single card from the top of the deck."""
        return self.deal(1)[0]

    def burn(self):
        """Burn (discard) the top card."""
        if self.cards:
            self.cards.pop(0)

    def __len__(self) -> int:
        """Number of cards remaining in the deck."""
        return len(self.cards)

    def __str__(self) -> str:
        """String representation of the deck."""
        return f"Deck({len(self.cards)} cards)"
