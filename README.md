# TickAlert - Telegram Bot

**TickAlert** היא פלטפורמה לשליחת **התראות בזמן אמת** על כרטיסים שמתפנים לאירועים סולד־אאוט.

כאשר אוהד או משתמש מפרסם שיש לו כרטיס למכירה, המערכת שולחת **התראה מיידית** לכל מי שנרשם לאותו אירוע, כדי שלא יפספס את ההזדמנות.

המערכת פועלת כבוט בטלגרם, ללא תיווך או תשלום, ומתחילה במשחקי כדורגל (בית״ר ירושלים), אך בנויה כתשתית כללית שניתן להרחיב לכל סוגי האירועים.

## הערך המרכזי

לא לחפש כרטיסים – לקבל התראה ברגע שהם זמינים! ⚡

## Features

- 🔔 **התראות מיידיות** - קבל התראה ברגע שמישהו מפרסם כרטיס
- 📅 **ניהול אירועים** - הירשם לאירועים שמעניינים אותך
- 🎫 **פרסום כרטיסים** - פרסם כרטיסים למכירה בקלות
- 🛡️ **מניעת ספאם** - הגבלת פרסומים יומית (5 כרטיסים ביום)
- 📊 **מעקב אישי** - צפה בהרשמות והכרטיסים שלך
- 🇮🇱 **תמיכה בעברית** - ממשק מלא בעברית
- 🤖 **בוט טלגרם** - מבוסס על aiogram 3.x
- 💾 **SQLite** - מסד נתונים מקומי
- 🐳 **Docker** - תמיכה מלאה ב-Docker
- 🚂 **Railway** - מוכן לפריסה ב-Railway

## Prerequisites

- Python 3.11+
- Docker (אופציונלי, לפריסה מקומית)
- Telegram Bot Token (קבל מ-[@BotFather](https://t.me/BotFather))

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/prielc/TickAlert.git
cd TickAlert
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

צור קובץ `.env` בתיקיית השורש:

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

ראה את [DEPLOY.md](DEPLOY.md) להוראות פריסה מפורטות.

בקצרה:
1. העלה את הקוד ל-GitHub
2. התחבר ל-[Railway](https://railway.app)
3. בחר "Deploy from GitHub repo"
4. הוסף את משתנה הסביבה `BOT_TOKEN`
5. Railway יבנה ויפרס אוטומטית

## Available Commands

### אירועים והרשמות
- `/events` - רשימת כל האירועים הזמינים
- `/subscribe <מספר_אירוע>` - הירשם לאירוע
- `/unsubscribe <מספר_אירוע>` - בטל הרשמה לאירוע
- `/mysubscriptions` - האירועים שאתה רשום אליהם

### כרטיסים
- `/postticket` - פרסם כרטיס למכירה (תהליך אינטראקטיבי)
- `/mytickets` - הכרטיסים שפרסמת

### אחר
- `/start` - התחל את הבוט
- `/help` - הצג הודעת עזרה
- `/stats` - סטטיסטיקות אישיות

## How It Works

1. **הרשמה לאירועים**: המשתמש נרשם לאירועים שמעניינים אותו באמצעות `/subscribe`
2. **פרסום כרטיס**: כשמישהו מפרסם כרטיס באמצעות `/postticket`, המערכת שולחת התראה מיידית
3. **התראות**: כל המנויים לאירוע מקבלים התראה עם פרטי הכרטיס ופרטי קשר
4. **מניעת ספאם**: הגבלה של 5 כרטיסים ביום למשתמש

## Database Schema

הבוט משתמש ב-SQLite עם הטבלאות הבאות:

- **users** - משתמשים
- **events** - אירועים
- **subscriptions** - הרשמות משתמשים לאירועים
- **tickets** - כרטיסים שפורסמו למכירה
- **notifications** - לוג של התראות שנשלחו
- **rate_limits** - הגבלות למניעת ספאם

המסד נתונים נשמר ב-`data/bot.db` ונוצר אוטומטית בעת ההפעלה הראשונה.

## Project Structure

```
TickAlert/
├── bot.py              # Main bot application
├── handlers.py         # Message handlers (Hebrew UI)
├── database.py         # Database operations
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── railway.json        # Railway deployment config
├── DEPLOY.md           # Deployment guide
├── .env                # Environment variables (not in git)
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Development

להרחבת הבוט:

1. הוסף handlers חדשים ב-`handlers.py`
2. הוסף פעולות מסד נתונים ב-`database.py`
3. הוסף אירועים חדשים באמצעות `db.add_event()`

## Default Events

הבוט מגיע עם אירועים ברירת מחדל:
- בית״ר ירושלים - משחק בית
- בית״ר ירושלים - משחק חוץ

ניתן להוסיף אירועים נוספים בקוד או דרך מסד הנתונים.

## License

MIT

## Contributing

תרומות יתקבלו בברכה! פתח issue או pull request.
