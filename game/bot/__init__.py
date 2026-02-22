"""Bot AI package for Texas Hold'em Poker."""

from .base import BotBase, BotDifficulty
from .easy import EasyBot
from .medium import MediumBot
from .hard import HardBot


def create_bot(difficulty: BotDifficulty, name: str = None, chips: int = 1000):
    """Factory function to create a bot of specified difficulty."""
    if difficulty == BotDifficulty.EASY:
        return EasyBot(name or "Fish", chips)
    elif difficulty == BotDifficulty.MEDIUM:
        return MediumBot(name or "Shark", chips)
    elif difficulty == BotDifficulty.HARD:
        return HardBot(name or "Pro", chips)
    else:
        raise ValueError(f"Unknown difficulty: {difficulty}")


__all__ = [
    'BotBase', 'BotDifficulty',
    'EasyBot', 'MediumBot', 'HardBot',
    'create_bot'
]
