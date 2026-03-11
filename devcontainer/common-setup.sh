#!/bin/bash
# Shared setup for all devcontainers — runs in onCreateCommand

set -e

# Set UTF-8 locale system-wide
echo "Configuring UTF-8 locale..."
sudo tee /etc/default/locale > /dev/null << 'LOCALE'
LANG=en_US.UTF-8
LC_ALL=en_US.UTF-8
LOCALE
sudo tee /etc/profile.d/locale.sh > /dev/null << 'PROF'
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
PROF

# Fix volume permissions (Docker volumes default to root ownership)
echo "Fixing volume permissions..."
sudo chown -R neo:neo /commandhistory
sudo chown -R neo:neo /home/neo/.claude

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
