#!/bin/bash
if [ ! -d "extensions" ]; then
  git clone https://github.com/Fu-Jie/openwebui-extensions.git extensions
fi

PORT=${PORT:-5000}
open-webui serve --host 0.0.0.0 --port $PORT
