# Poker

A terminal-based Texas Hold'em Poker game with AI opponents.

![Poker Demo](screenshots/demo.gif)

## Features

- **1-3 AI Opponents** - Play heads-up or at a full 4-handed table
- **3 Difficulty Levels**
  - Easy - Loose passive "fish" that calls too much
  - Medium - Tight aggressive "shark" with solid fundamentals
  - Hard - Near-GTO play with opponent exploitation
- **Full Poker Experience**
  - Pre-flop, Flop, Turn, River betting rounds
  - Proper blind structure and dealer rotation
  - All-in situations and side pots
- **Real-time Odds** - See your win probability and hand odds
- **Hand Rankings Reference** - Built-in guide for beginners
- **Beautiful Terminal UI** - Unicode cards with color suits

## Installation

### Homebrew (macOS)

```bash
brew tap tvyomkesh/poker
brew install poker
```

### pip (All platforms)

```bash
pip install fairpoker
```

### From source

```bash
git clone https://github.com/tvyomkesh/poker.git
cd poker
pip install -e .
```

## Usage

```bash
# If installed via brew or pip:
poker

# Or:
fairpoker

# From source:
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| `C` | Check (when no bet) / Call (when facing bet) |
| `R` | Raise / Bet |
| `F` | Fold |
| `Q` | Quit |
| `N` | Next hand (after showdown) |

## Requirements

- **Terminal Size**: 140 x 40 minimum
- **Python**: 3.8 or higher
- **Platform**: macOS, Linux, Windows (with windows-curses)

## How to Play

1. **Select difficulty** - Choose Easy, Medium, or Hard opponents
2. **Select number of bots** - Play against 1, 2, or 3 AI players
3. **Play poker!** - Standard Texas Hold'em rules apply:
   - Each player gets 2 hole cards
   - 5 community cards are dealt (3 on flop, 1 on turn, 1 on river)
   - Best 5-card hand wins
   - Bet, raise, call, or fold your way to victory!

## Hand Rankings (Best to Worst)

1. **Royal Flush** - A K Q J 10 same suit
2. **Straight Flush** - 5 consecutive, same suit
3. **Four of a Kind** - 4 cards same rank
4. **Full House** - 3 of a kind + pair
5. **Flush** - 5 cards same suit
6. **Straight** - 5 consecutive cards
7. **Three of a Kind** - 3 cards same rank
8. **Two Pair** - 2 different pairs
9. **One Pair** - 2 cards same rank
10. **High Card** - Highest card wins

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Vyomkesh Tripathi

---

*Made with Python and curses. No actual gambling involved!*
