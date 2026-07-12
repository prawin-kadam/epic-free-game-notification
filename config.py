"""
Configuration constants for the Epic Games Free Games Notifier.

All secrets (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) are read from
environment variables at runtime — never hardcode them here.
"""

# ---------------------------------------------------------------------------
# Epic Games Store API
# ---------------------------------------------------------------------------
# Official GraphQL-backed promotional endpoint used by the EGS website.
# Replace this URL if Epic changes their API in the future.
EPIC_API_URL: str = (
    "https://store-site-backend-static.ak.epicgames.com"
    "/freeGamesPromotions"
)

# Query parameters accepted by the endpoint
EPIC_API_PARAMS: dict = {
    "locale": "en-US",
    "country": "US",
    "allowCountries": "US",
}

# Public-facing store URL used in notifications
EPIC_STORE_URL: str = "https://store.epicgames.com/en-US/free-games"

# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
# JSON file that stores the last-known list of free games.
# This file is committed back to the repository by the GitHub Action so that
# state is preserved across workflow runs.
LAST_GAMES_FILE: str = "last_games.json"