
# Uptime Monitoring Telegram Bot
A Telegram bot that monitors websites and notifies you of their status.



## Features

- Add websites to monitor.
- Receive notifications if a website goes down or comes back up.
- Check the status of all monitored websites.
- Public access, allowing any Telegram user to use the bot.


## Deployment

### VPS

To deploy this project run

```bash
  git clone https://github.com/irymee/UptimeRobot.gitUp
  cd UptimeRobot
  pip install -r requirements.txt
  python3 bot.py
```

### Docker Deployment:
```bash
docker build -t uptime-bot
```
```bash
docker run -e API_ID='your_value' -e API_HASH='your_value' -e BOT_TOKEN='your_value' -e DB_URI='your_value' uptime-bot
```


### Render
- Push the bot to a GitHub repository.
- Set up a new service on Render and link to the repository.
- Define environment variables (`API_ID`, `API_HASH`, `BOT_TOKEN`, `DB_URI`) on the Render dashboard.
- Deploy!

