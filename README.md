# TickAlert Telegram Bot

A Telegram bot built with Python, aiogram, and SQLite.

## Features

- 🤖 Telegram bot using aiogram 3.x
- 📊 SQLite database for data persistence
- 🐳 Docker support for containerization
- 🚂 Railway deployment ready
- 📝 Long polling (no webhook needed)

## Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- Telegram Bot Token (get it from [@BotFather](https://t.me/BotFather))

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd TickAlert
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```bash
BOT_TOKEN=your_telegram_bot_token_here
```

### 4. Run locally

```bash
python bot.py
```

## Docker Setup

### Build and run with Docker

```bash
docker-compose up --build
```

### Or build and run manually

```bash
docker build -t tickalert-bot .
docker run --env-file .env tickalert-bot
```

## Railway Deployment

1. Install Railway CLI (optional):
   ```bash
   npm i -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

3. Initialize project:
   ```bash
   railway init
   ```

4. Add environment variable:
   ```bash
   railway variables set BOT_TOKEN=your_telegram_bot_token_here
   ```

5. Deploy:
   ```bash
   railway up
   ```

Or use the Railway web interface:
- Connect your GitHub repository
- Add `BOT_TOKEN` as an environment variable
- Railway will automatically detect the Dockerfile and deploy

## Project Structure

```
TickAlert/
├── bot.py              # Main bot application
├── handlers.py         # Message handlers
├── database.py         # Database operations
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── railway.json        # Railway deployment config
├── .env                # Environment variables (not in git)
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Available Commands

- `/start` - Start the bot and register user
- `/help` - Show help message
- `/stats` - Show user statistics

## Database

The bot uses SQLite database stored in `data/bot.db`. The database is automatically initialized on first run.

## Development

To extend the bot:

1. Add new handlers in `handlers.py`
2. Add database operations in `database.py`
3. Register new routers in `bot.py`

## License

MIT
