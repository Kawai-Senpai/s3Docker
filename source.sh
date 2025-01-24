#!/bin/bash

# Add ~/.local/bin to PATH if it's not already included
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH=$PATH:$HOME/.local/bin' >> ~/.bashrc
    echo 'Added ~/.local/bin to PATH in ~/.bashrc'
else
    echo '~/.local/bin is already in PATH'
fi

# Apply the changes
source ~/.bashrc
