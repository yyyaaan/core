# Browser Automation

## Chrome Remote Debug on Containers or on External Machines

see root

### Hybrid mode: Local Browser + Container Python Runtime

Quick start the dev env, by start the dev contaienr in VSCode (or others)

```
uv run autobrowser
# or
uv run python -m autobrowser.main
```

```
# any reachable web
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=$HOME/Lab/z-debug-profile

"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome_debug" --no-first-run

# chrome://inspect/#remote-debugging
# localhost:92222/json/version
```
