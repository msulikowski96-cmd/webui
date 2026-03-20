#!/bin/bash

# pobierz extensions jeśli nie istnieją
if [ ! -d "extensions" ]; then
  git clone https://github.com/Fu-Jie/openwebui-extensions.git extensions
fi

python main.py
