#!/bin/bash
if [ ! -d "extensions" ]; then
  git clone https://github.com/Fu-Jie/openwebui-extensions.git extensions
fi

open-webui serve --host 0.0.0.0 --port 5000