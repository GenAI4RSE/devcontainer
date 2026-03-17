#!/bin/bash
# Shared setup for all devcontainers — runs in onCreateCommand

set -e

# Install git-delta (non-fatal — network may be slow)
echo "Installing git-delta ${GIT_DELTA_VERSION}..."
ARCH=$(dpkg --print-architecture)
if curl -fSL --retry 2 --connect-timeout 5 --max-time 30 \
  "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" \
  -o /tmp/git-delta.deb; then
  sudo dpkg -i /tmp/git-delta.deb
  rm -f /tmp/git-delta.deb
  echo "git-delta installed successfully."
else
  echo "WARNING: git-delta installation failed (network issue?). Skipping."
  rm -f /tmp/git-delta.deb
fi

# Fix volume permissions (Docker volumes default to root ownership)
echo "Fixing volume permissions..."
sudo chown -R neo:neo /commandhistory