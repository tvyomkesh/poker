class Poker < Formula
  desc "Terminal-based Texas Hold'em Poker game with AI opponents"
  homepage "https://github.com/tvyomkesh/poker"
  url "https://github.com/tvyomkesh/poker/archive/refs/tags/v1.2.0.tar.gz"
  sha256 "2b245c6013283f49afd1883c6f05a49147e6ab5b83780984c1f423bbda76ff9e"
  license "MIT"

  depends_on "python@3.12" => :recommended

  def install
    # Install all Python files to libexec
    libexec.install Dir["*"]

    # Create executable wrapper that finds available Python 3.8+
    wrapper_script = <<~EOS
      #!/bin/bash
      # Find a suitable Python version (3.8+)
      for py in python3.14 python3.13 python3.12 python3.11 python3.10 python3.9 python3.8 python3; do
        if command -v "$py" &> /dev/null; then
          version=$("$py" -c "import sys; print(sys.version_info[:2] >= (3, 8))" 2>/dev/null)
          if [ "$version" = "True" ]; then
            PYTHON="$py"
            break
          fi
        fi
      done

      if [ -z "$PYTHON" ]; then
        echo "Error: Python 3.8+ is required but not found."
        echo "Install Python via: brew install python@3.12"
        exit 1
      fi

      cd "#{libexec}"
      exec "$PYTHON" -c "from main import main; main()" "$@"
    EOS

    (bin/"fairpoker").write wrapper_script
    (bin/"poker").write wrapper_script
  end

  test do
    system "true"
  end
end
