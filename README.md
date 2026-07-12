# 🎮 Epic Games Free Games Notifier

A lightweight Python automation that checks the Epic Games Store every 6 hours and sends you a **Telegram notification** whenever a new free game becomes available — with no paid hosting required.

---

## ✨ Features

- Checks Epic's official promotions API (no web scraping)
- Sends a Telegram message **only when the free game list changes**
- Deduplicates notifications — no spam for the same game
- Runs entirely via **GitHub Actions** (free tier is sufficient)
- Persists state via a committed `last_games.json` file
- Handles API failures with automatic retries and graceful exits

---

## 📁 Folder Structure

```
epic-games-notifier/
│
├── main.py              # Core logic
├── config.py            # API endpoints and constants
├── requirements.txt     # Python dependencies
├── last_games.json      # Persisted state (committed by CI)
├── README.md
├── .gitignore
│
└── .github/
    └── workflows/
        └── notify.yml   # GitHub Actions workflow
```

---

## 🚀 Installation & Setup

### 1. Fork / Clone this repository

```bash
git clone https://github.com/YOUR_USERNAME/epic-games-notifier.git
cd epic-games-notifier
```

### 2. Create a Python virtual environment (local runs only)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🤖 Telegram Bot Setup

1. Open Telegram and search for **@BotFather**.
2. Send `/newbot` and follow the prompts to create your bot.
3. Copy the **Bot Token** (looks like `123456:ABC-DEF...`).
4. Start a conversation with your new bot (send it `/start`).
5. Get your **Chat ID** by visiting:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Look for `"chat": {"id": <YOUR_CHAT_ID>}` in the response.

---

## 🔑 GitHub Secrets Setup

In your GitHub repository go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret name           | Value                    |
|-----------------------|--------------------------|
| `TELEGRAM_BOT_TOKEN`  | Your bot token           |
| `TELEGRAM_CHAT_ID`    | Your chat / user ID      |

---

## 💻 Running Locally

Export the secrets as environment variables, then run:

```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

python main.py
```

To force a notification on the first run, make sure `last_games.json` contains `[]`.

---

## ⚙️ GitHub Actions Explained

The workflow file (`.github/workflows/notify.yml`) does the following:

| Step | What happens |
|------|-------------|
| **Trigger** | Runs every 6 hours via cron, or manually via `workflow_dispatch` |
| **Checkout** | Clones the repo including the current `last_games.json` |
| **Python setup** | Installs Python 3.12 with pip caching |
| **Install deps** | `pip install -r requirements.txt` |
| **Run script** | Executes `main.py` with secrets injected as env vars |
| **Commit JSON** | Commits `last_games.json` back to the repo **only if it changed** |

The `[skip ci]` tag in the commit message prevents the commit itself from triggering another workflow run.

---

## 🔔 Notification Example

```
🎮 New Epic Games Free Titles!

• Control
• Deathloop

Claim them before the offer expires.

Epic Games Store
```

---

## 🛠 Future Improvements

The codebase is structured to make these easy to add:

- **Discord / Slack / Email notifications** — add a new `notify_discord()` function alongside `send_telegram_message()`
- **Multiple Telegram recipients** — iterate over a list of chat IDs
- **Steam / GOG / Prime Gaming** — add new `fetch_*` and `extract_*` functions and call them in `main()`
- **Daily digest mode** — accumulate changes over the day, send a single summary
- **Unit tests** — each function is independently testable with `pytest`

---

## 📄 License

MIT — do whatever you like with it.
