
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
  git clone https://github.com/irymee/UptimeRobot.git
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

## Heroku Deployment:
You can easily deploy the bot to Heroku with the following steps:

1. **Fork the Repository**: Start by forking this repository to your GitHub account.

2. **Create a New Heroku App**: Navigate to your [Heroku Dashboard](https://dashboard.heroku.com/) and create a new app.

3. **Connect to GitHub**: In your Heroku app dashboard, go to the "Deploy" tab, choose "GitHub" as the deployment method, and connect your repository.

4. **Set Environment Variables**: In the "Settings" tab of your Heroku app dashboard, reveal "Config Vars" and set the necessary environment variables: `API_ID`, `API_HASH`, `BOT_TOKEN`, and `DB_URI`.

5. **Deploy with One-Click**: Alternatively, click the button below to deploy directly:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/irymee/UptimeRobot)


## Contributing

Contributions are always welcome!
