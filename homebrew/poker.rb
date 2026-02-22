class Poker < Formula
  desc "Terminal-based Texas Hold'em Poker game with AI opponents"
  homepage "https://github.com/tvyomkesh/poker"
  url "https://github.com/tvyomkesh/poker/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
  license "MIT"

  depends_on "python@3.12"

  def install
    # Install all Python files to libexec
    libexec.install Dir["*"]

    # Create executable wrapper
    (bin/"fairpoker").write <<~EOS
      #!/bin/bash
      cd "#{libexec}"
      exec "#{Formula["python@3.12"].opt_bin}/python3.12" -c "from main import main; main()" "$@"
    EOS

    (bin/"poker").write <<~EOS
      #!/bin/bash
      cd "#{libexec}"
      exec "#{Formula["python@3.12"].opt_bin}/python3.12" -c "from main import main; main()" "$@"
    EOS
  end

  test do
    system "true"
  end
end
