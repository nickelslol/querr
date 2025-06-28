#!/usr/bin/env python3
import requests
import time

# ─── Configuration ─────────────────────────────────────────────────────────────
SONARR_URL     = "http://localhost:8989"   # e.g. http://127.0.0.1:8989
SONARR_API_KEY = "YOUR_SONARR_API_KEY"
POLL_INTERVAL  = 60  # seconds between checks
# ────────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "X-Api-Key": SONARR_API_KEY,
    "Content-Type": "application/json"
}

def get_queue():
    """Fetch the full Sonarr queue."""
    resp = requests.get(f"{SONARR_URL}/api/v3/queue", headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("records", [])

def should_remove(item):
    """
    Return True if this item completed downloading but
    didn't import due to not being an upgrade.
    """
    if item.get("status") != "completed":
        return False

    # Case A: Sonarr logged an import failure with a custom-format message
    err = item.get("errorMessage") or ""
    if "Custom format score" in err or "not an upgrade" in err:
        return True

    # Case B: Quality cutoff not met
    if item.get("qualityCutoffNotMet"):
        return True

    # Case C: Sonarr marks it as not an upgrade
    if item.get("isUpgrade") is False:
        return True

    return False

def remove_queue_item(item_id):
    """
    DELETE the queue entry but leave the download in the client.
    removeFromClient=false is key here.
    """
    params = { "removeFromClient": "false" }
    url = f"{SONARR_URL}/api/v3/queue/{item_id}"
    resp = requests.delete(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    print(f"[Removed] Queue item {item_id}")

def main_loop():
    print("Starting Sonarr queue monitor...")
    while True:
        try:
            queue = get_queue()
            for itm in queue:
                if should_remove(itm):
                    remove_queue_item(itm["id"])
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main_loop()
