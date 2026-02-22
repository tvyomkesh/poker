class Poker < Formula
  desc "Terminal-based Texas Hold'em Poker game with AI opponents"
  homepage "https://github.com/tvyomkesh/poker"
  url "https://github.com/tvyomkesh/poker/archive/refs/tags/v1.1.0.tar.gz"
  sha256 "e438dcceb0c9f08781961c35eb557f1ce3d75dedb1d759a79f2d3e28ad0f2c9e"
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
