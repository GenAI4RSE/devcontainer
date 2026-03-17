# oh-my-zsh plugins
sed -i 's/^plugins=.*/plugins=(git)/' ~/.zshrc

# Custom settings appended to .zshrc
cat >> ~/.zshrc << 'EOF'

# Timestamp format for history
HIST_STAMPS="yyyy-mm-dd"

# autojump
[ -f /usr/share/autojump/autojump.sh ] && . /usr/share/autojump/autojump.sh

# bat is installed as batcat on Ubuntu
alias bat="batcat"
EOF
