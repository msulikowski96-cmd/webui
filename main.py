import os
import sys

# dodanie extensions do path
EXTENSIONS_PATH = os.path.join(os.getcwd(), "extensions")
if EXTENSIONS_PATH not in sys.path:
    sys.path.append(EXTENSIONS_PATH)

from open_webui import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)