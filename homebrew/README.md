# Homebrew Installation for Poker

## Setup Instructions

To make `brew install poker` work, you need to create a Homebrew Tap:

### Step 1: Create a new GitHub repository

Create a repository named `homebrew-poker` (must start with `homebrew-`).

```bash
# On GitHub, create: https://github.com/vyomkesh/homebrew-poker
```

### Step 2: Add the formula

Copy `poker.rb` to the new repository:

```
homebrew-poker/
└── Formula/
    └── poker.rb
```

### Step 3: Create a release tag in the main repo

```bash
cd /path/to/poker
git tag v1.0.0
git push origin v1.0.0
```

### Step 4: Get the SHA256 hash

```bash
# Download the tarball and get its hash
curl -sL https://github.com/vyomkesh/poker/archive/refs/tags/v1.0.0.tar.gz | shasum -a 256
```

Update the `sha256` line in `poker.rb` with the actual hash.

### Step 5: Users can now install

```bash
# Add your tap
brew tap vyomkesh/poker

# Install the game
brew install poker

# Or in one command
brew install vyomkesh/poker/poker
```

## Alternative: Install with pip

```bash
# Install with pip (works on any system with Python 3.8+)
pip install fairpoker

# Or install from GitHub directly
pip install git+https://github.com/vyomkesh/poker.git
```
