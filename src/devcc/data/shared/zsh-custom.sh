# oh-my-zsh plugins
sed -i 's/^plugins=.*/plugins=(git)/' ~/.zshrc

# Custom settings appended to .zshrc
cat >> ~/.zshrc << 'EOF'

# Timestamp format for history
HIST_STAMPS="yyyy-mm-dd"

# autojump
[ -f /usr/share/autojump/autojump.sh ] && . /usr/share/autojump/autojump.sh

# Alias
alias bat="batcat"
alias cls='clear'
alias ll='ls -alF'
EOF
