import os
import sys

EXTENSIONS_PATH = os.path.join(os.getcwd(), "extensions")
if EXTENSIONS_PATH not in sys.path:
    sys.path.append(EXTENSIONS_PATH)

if __name__ == "__main__":
    import uvicorn
    from open_webui.main import app
    uvicorn.run(app, host="0.0.0.0", port=5000)
