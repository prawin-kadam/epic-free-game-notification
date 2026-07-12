"""
Epic Games Free Games Notifier
Checks for free games on the Epic Games Store and sends Telegram notifications.
"""

import json
import logging
import os
import sys
import time
from typing import Optional

import requests

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def fetch_free_games(retries: int = 3, backoff: float = 2.0) -> Optional[dict]:
    """
    Fetch current promotions from the Epic Games Store API.

    Args:
        retries: Number of retry attempts on failure.
        backoff: Base seconds to wait between retries (exponential).

    Returns:
        Parsed JSON response dict, or None if all attempts fail.
    """
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Fetching free games from Epic API (attempt {attempt}/{retries})...")
            response = requests.get(
                config.EPIC_API_URL,
                params=config.EPIC_API_PARAMS,
                timeout=15,
            )
            response.raise_for_status()
            logger.info("Successfully fetched data from Epic API.")
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.warning(f"Request failed: {exc}")
            if attempt < retries:
                wait = backoff ** attempt
                logger.info(f"Retrying in {wait:.0f} seconds...")
                time.sleep(wait)

    logger.error("All retry attempts exhausted. Could not reach Epic Games API.")
    return None


def extract_current_games(data: dict) -> list[dict]:
    """
    Extract games that are currently free (active promotional offer).

    Args:
        data: Raw JSON response from the Epic Games API.

    Returns:
        List of dicts with 'title' and 'url' keys for each free game.
    """
    free_games: list[dict] = []

    try:
        elements = data["data"]["Catalog"]["searchStore"]["elements"]
    except (KeyError, TypeError):
        logger.error("Unexpected API response structure; could not extract games.")
        return free_games

    for element in elements:
        title = element.get("title", "Unknown Title")
        promotions = element.get("promotions") or {}
        offers = promotions.get("promotionalOffers", [])

        for offer_group in offers:
            for offer in offer_group.get("promotionalOffers", []):
                discount = offer.get("discountSetting", {})
                if discount.get("discountPercentage", -1) == 0:
                    # Build the store URL from the product slug
                    slug = (
                        element.get("productSlug")
                        or element.get("urlSlug")
                        or ""
                    )
                    slug = slug.replace("/home", "")
                    url = f"{config.EPIC_STORE_URL}/p/{slug}" if slug else config.EPIC_STORE_URL
                    free_games.append({"title": title, "url": url})
                    break  # Avoid duplicates from multiple active offers

    logger.info(f"Found {len(free_games)} free game(s) currently available.")
    return free_games


def load_previous_games() -> list[dict]:
    """
    Load the previously saved list of free games from disk.

    Returns:
        List of game dicts from the last run, or empty list if file is missing/corrupt.
    """
    if not os.path.exists(config.LAST_GAMES_FILE):
        logger.info("No previous games file found; treating as first run.")
        return []

    try:
        with open(config.LAST_GAMES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} game(s) from '{config.LAST_GAMES_FILE}'.")
            return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(f"Could not read '{config.LAST_GAMES_FILE}': {exc}. Starting fresh.")
        return []


def games_changed(current: list[dict], previous: list[dict]) -> bool:
    """
    Determine whether the free game list has changed since the last run.

    Comparison is done by game title only to avoid URL drift between runs.

    Args:
        current: Games fetched in this run.
        previous: Games saved from the previous run.

    Returns:
        True if the lists differ, False otherwise.
    """
    current_titles = {g["title"] for g in current}
    previous_titles = {g["title"] for g in previous}
    changed = current_titles != previous_titles
    if changed:
        added = current_titles - previous_titles
        removed = previous_titles - current_titles
        if added:
            logger.info(f"New free game(s): {', '.join(added)}")
        if removed:
            logger.info(f"Expired game(s): {', '.join(removed)}")
    else:
        logger.info("Free game list is unchanged.")
    return changed


def build_notification_message(games: list[dict]) -> str:
    """
    Build the Telegram notification message.

    Args:
        games: List of currently free games.

    Returns:
        Formatted notification string.
    """
    if not games:
        return "🎮 No free games are available on Epic Games Store right now."

    lines = ["🎮 *New Epic Games Free Titles!*", ""]
    for game in games:
        lines.append(f"• {game['title']}")
    lines += [
        "",
        "Claim them before the offer expires\\.",
        "",
        f"[Epic Games Store]({config.EPIC_STORE_URL})",
    ]
    return "\n".join(lines)


def send_telegram_message(text: str) -> bool:
    """
    Send a message via the Telegram Bot API.

    Args:
        text: The message text (supports MarkdownV2).

    Returns:
        True if the message was sent successfully, False otherwise.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        logger.error(
            "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set. "
            "Add them as GitHub Secrets (or environment variables for local runs)."
        )
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Telegram notification sent successfully.")
        return True
    except requests.exceptions.RequestException as exc:
        logger.error(f"Failed to send Telegram message: {exc}")
        return False


def save_current_games(games: list[dict]) -> bool:
    """
    Persist the current free game list to disk.

    Args:
        games: List of game dicts to save.

    Returns:
        True on success, False on failure.
    """
    try:
        with open(config.LAST_GAMES_FILE, "w", encoding="utf-8") as f:
            json.dump(games, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(games)} game(s) to '{config.LAST_GAMES_FILE}'.")
        return True
    except OSError as exc:
        logger.error(f"Failed to save games file: {exc}")
        return False


def main() -> None:
    """
    Main entry point: orchestrates the fetch → compare → notify → save pipeline.
    """
    logger.info("=== Epic Games Free Games Notifier starting ===")

    # 1. Fetch current free games from the API
    raw_data = fetch_free_games()
    if raw_data is None:
        logger.error("Aborting: could not retrieve data from the Epic Games API.")
        sys.exit(1)

    # 2. Extract only currently free games
    current_games = extract_current_games(raw_data)

    # 3. Load the previously saved games
    previous_games = load_previous_games()

    # 4. Check if anything changed
    if not games_changed(current_games, previous_games):
        logger.info("Nothing to do. Exiting.")
        return

    # 5. Send Telegram notification
    message = build_notification_message(current_games)
    send_telegram_message(message)

    # 6. Persist updated list (only on successful fetch)
    save_current_games(current_games)

    logger.info("=== Run complete ===")


if __name__ == "__main__":
    main()