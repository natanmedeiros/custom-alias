class DynamicAlias < Formula
  include Language::Python::Virtualenv

  desc "A dynamic alias builder for command line power users"
  homepage "https://github.com/natanmedeiros/custom-alias"
  url "https://github.com/natanmedeiros/custom-alias/archive/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256"
  license "MIT"

  depends_on "python@3.8"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/dya", "--help"
  end
end
