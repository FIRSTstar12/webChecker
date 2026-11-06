import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import hashlib
import difflib

# ===== CONFIGURATION =====

URL = "https://www.coloradohighschoolmocktrial.com/"
CHECK_INTERVAL = 30

# Paste your Discord webhook URL here
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1566306380187701359/vsRcew_4P5B-Wx_g3pWT-VA85G_zS0HjMpNiw7y8WS0S94P_u2ns2V-M9ypZU7t698Ov"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; WebsiteChangeWatcher/1.0)"
}


def get_website_text():
    """Fetch the website and extract its text."""

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup(
        ["script", "style", "noscript", "svg"]
    ):
        element.decompose()

    return soup.get_text(separator=" ", strip=True)


def get_hash(text):
    """Generate a fingerprint of the website text."""

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def send_discord_notification(old_text, new_text):
    """Send a Discord notification describing the change."""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    old_words = old_text.split()
    new_words = new_text.split()

    diff = list(difflib.unified_diff(
        old_words,
        new_words,
        fromfile="Previous",
        tofile="Current",
        lineterm="",
        n=3
    ))

    # Keep messages within Discord's message-length limit.
    diff_text = "\n".join(diff)

    if len(diff_text) > 1200:
        diff_text = diff_text[:1200] + "\n... (truncated)"

    message = (
        f"🚨 **Website Text Changed!**\n"
        f"**Website:** {URL}\n"
        f"**Detected:** {timestamp}\n\n"
        f"**Text differences:**\n"
        f"```diff\n{diff_text}\n```"
    )

    # Discord limits message content to 2000 characters.
    if len(message) > 1900:
        message = message[:1850] + "\n... (truncated)"

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={
            "content": message,
            "allowed_mentions": {"parse": []}
        },
        timeout=20
    )

    response.raise_for_status()

    print("Discord notification sent!")


def main():
    print("=" * 45)
    print("       WEBSITE CHANGE WATCHER")
    print("=" * 45)
    print(f"Website: {URL}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("Press Ctrl+C to stop.\n")

    previous_text = None

    try:
        while True:
            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            try:
                current_text = get_website_text()

                if previous_text is None:
                    previous_text = current_text

                    with open(
                        "website_text.txt",
                        "w",
                        encoding="utf-8"
                    ) as file:
                        file.write(current_text)

                    print(f"[{timestamp}] Initial page loaded.")

                elif get_hash(current_text) != get_hash(previous_text):
                    print(f"[{timestamp}] WEBSITE CHANGED!")

                    try:
                        send_discord_notification(
                            previous_text,
                            current_text
                        )

                        with open(
                            "website_text.txt",
                            "w",
                            encoding="utf-8"
                        ) as file:
                            file.write(current_text)

                        previous_text = current_text

                    except requests.RequestException as error:
                        print(
                            f"Notification failed: {error}"
                        )

                else:
                    print(f"[{timestamp}] No changes detected.")

            except requests.RequestException as error:
                print(f"[{timestamp}] Website request failed: {error}")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\nWatcher stopped.")


if __name__ == "__main__":
    main()