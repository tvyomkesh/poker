#!/bin/bash
# Record a demo of the poker game for the README

echo "=== Poker Demo Recording ==="
echo ""
echo "This will record your terminal session with asciinema."
echo "Play a quick game (1-2 hands), then press Ctrl+D or type 'exit' to stop."
echo ""
echo "Tips for a good demo:"
echo "  - Choose Hard difficulty (looks impressive)"
echo "  - Pick 2 or 3 bots"
echo "  - Play 1-2 hands showing raises, calls, folds"
echo "  - Show a showdown with winning hand"
echo ""
echo "Press Enter to start recording..."
read

# Record to file
asciinema rec demo.cast --title "Poker - Terminal Texas Hold'em" --idle-time-limit 2

echo ""
echo "Recording saved to demo.cast"
echo ""
echo "To upload and get a link:"
echo "  asciinema upload demo.cast"
echo ""
echo "Or to create a GIF (if you have agg installed):"
echo "  agg demo.cast demo.gif"
