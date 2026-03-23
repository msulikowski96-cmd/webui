# OpenWebUI Extensions

## Overview
This project runs **Open WebUI** (v0.8.10) — an AI chat interface platform — with a suite of custom plugins and extensions. The extensions are organized as a collection of Python-based plugins for OpenWebUI covering actions, filters, pipes, and tools.

## Architecture
- **Backend**: OpenWebUI (FastAPI + uvicorn) running on port 5000
- **Database**: PostgreSQL (Replit managed, connected via `DATABASE_URL` env var)
- **Extensions**: Located in the `extensions/` directory (Python plugins for OpenWebUI)
- **Mobile App**: Expo React Native app in `webui-android/` that wraps OpenWebUI in a WebView
- **Entry point**: `start.sh` launches `open-webui serve --host 0.0.0.0 --port 5000`

## Key Files
- `start.sh` — shell script that starts OpenWebUI
- `main.py` — alternative Python entry point that adds extensions to path and runs uvicorn
- `requirements.txt` — Python dependencies
- `extensions/` — OpenWebUI plugins (actions, filters, pipes, tools)
- `webui-android/` — Expo React Native mobile app (WebView wrapper)
  - `webui-android/App.tsx` — main app component with WebView
  - `webui-android/app.json` — Expo configuration

## Dependencies

### Python (installed to `.pythonlibs/`):
- `open-webui==0.8.10`
- `psycopg2-binary` — PostgreSQL driver
- `langchain-community==0.4.1` (with manual `utils` stub for `langchain_community.utils.user_agent`)
- `numpy`, `opencv-python-headless`, `torch` (CPU)

### Node.js (in `webui-android/`):
- `expo` — React Native framework
- `react-native-webview` — WebView component
- `react-dom`, `react-native-web` — web preview support

## Workflows
- **Start application** — runs OpenWebUI on port 5000 (webview)
- **Start Mobile App** — runs Expo dev server on port 8080 (console, QR code for Expo Go)

## Notes
- The `langchain_community.utils` module is missing from v0.4.1 but required by open-webui. A stub was created at `.pythonlibs/lib/python3.11/site-packages/langchain_community/utils/`.
- The `WEBUI_SECRET_KEY` is loaded from `.webui_secret_key` file.
- CORS is set to `*` (all origins) which is expected for development.
- The mobile app URL in `webui-android/App.tsx` points to the Replit dev domain. Update it if the domain changes or after deployment.
