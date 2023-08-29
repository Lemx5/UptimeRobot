import datetime
import asyncio
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters
from quart import Quart, jsonify, request
import os

# Configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URI = os.getenv("DB_URI")
DB_NAME = os.getenv("DB_NAME", "uptimerobot")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "websites")
MAX_WEBSITES_PER_USER = int(os.getenv("MAX_WEBSITES_PER_USER", 10))
APP_URL = os.getenv("APP_URL")
ADMINS = [int(admin_id) for admin_id in os.getenv("ADMINS", "").split(",") if admin_id.isdigit()]

# Initialize
app = Client("uptime_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db_client = AsyncIOMotorClient(DB_URI)
db = db_client[DB_NAME]
collection = db[COLLECTION_NAME]

# Quart app initialization
web_app = Quart(__name__)

async def check_website(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                return response.status == 200
        except:
            return False

async def monitor_websites():
    while True:
        cursor = collection.find({})
        async for document in cursor:
            if (datetime.datetime.utcnow() - document["last_checked"]).total_seconds() >= document["interval"]:
                status = await check_website(document["url"])
                if status != document["status"] or (status and document["notify_up"]):
                    msg = f"🚨 {document['friendly_name']} ({document['url']}) is {'up' if status else 'down'} 🚨"
                    await app.send_message(document["chat_id"], msg)
                    await collection.update_one(
                        {"url": document["url"], "chat_id": document["chat_id"]},
                        {"$set": {"status": status, "last_checked": datetime.datetime.utcnow()}}
                    )
        await asyncio.sleep(30)

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    await message.reply(
        "Welcome to the Uptime Monitoring Bot! 🌐\n\n"
        "This bot monitors websites and notifies you of their status.\n"
        "Use /help to see available commands."
    )

@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    await message.reply(
        "Available Commands:\n\n"
        "/start - Start the bot and get a brief intro.\n"
        "/help - View this help message.\n"
        "/add <website_url> <interval_in_minutes> <friendly_name> - Add a website to the monitoring list.\n"
        "/remove <website_url> - Remove a website from the monitoring list.\n"
        "/status - Show the status of all monitored websites.\n"
        "/notify <website_url> - Toggle notifications for when a website is up.\n"
        "/history <website_url> - Show historical status data for a website."
    )

@app.on_message(filters.command("add") & filters.private)
async def add_website(client, message):
    try:
        data = message.text.split()
        url = data[1]
        interval = int(data[2]) * 60
        friendly_name = ' '.join(data[3:])

        user_websites = await collection.count_documents({"chat_id": message.chat.id})

        if message.chat.id not in ADMINS and user_websites >= MAX_WEBSITES_PER_USER:
            await message.reply(f"You have reached the limit of {MAX_WEBSITES_PER_USER} websites. Remove one to add another.")
            return
        
        status = await check_website(url)
        await collection.insert_one({
            "url": url,
            "status": status,
            "chat_id": message.chat.id,
            "interval": interval,
            "friendly_name": friendly_name,
            "notify_up": False,
            "last_checked": datetime.datetime.utcnow()
        })
        await message.reply(f"Added {friendly_name} ({url}) to monitoring list with interval {interval//60} minutes.")
    except Exception as e:
        await message.reply("Usage: `/add <website_url> <interval_in_minutes> <friendly_name>`\n\n" + str(e))

@app.on_message(filters.command("remove") & filters.private)
async def remove_website(client, message):
    url = message.text.split()[1]
    await collection.delete_one({"url": url, "chat_id": message.chat.id})
    await message.reply(f"Removed {url} from monitoring list.")

@app.on_message(filters.command("status") & filters.private)
async def show_status(client, message):
    cursor = collection.find({"chat_id": message.chat.id})
    msg = "🌐 Websites Status:\n"
    async for document in cursor:
        last_checked = document["last_checked"].strftime('%Y-%m-%d %H:%M:%S')
        msg += f"{document['friendly_name']} ({document['url']}) is {'🟢 up' if document['status'] else '🔴 down'} (Last checked: {last_checked})\n"
    await message.reply(msg)

@app.on_message(filters.command("notify") & filters.private)
async def toggle_notification(client, message):
    url = message.text.split()[1]
    document = await collection.find_one({"url": url, "chat_id": message.chat.id})
    if document:
        await collection.update_one({"url": url, "chat_id": message.chat.id}, {"$set": {"notify_up": not document["notify_up"]}})
        status = "ON" if not document["notify_up"] else "OFF"
        await message.reply(f"Notifications when {document['friendly_name']} ({url}) is up are now {status}")
    else:
        await message.reply("Website not found!")

# Historical data command
@app.on_message(filters.command("history") & filters.private)
async def show_history(client, message):
    url = message.text.split()[1]
    cursor = collection.find({"chat_id": message.chat.id, "url": url})
    msg = "📅 Historical Status for {}:\n".format(url)
    async for document in cursor:
        last_checked = document["last_checked"].strftime('%Y-%m-%d %H:%M:%S')
        msg += f"{document['friendly_name']} ({document['url']}): {'🟢 up' if document['status'] else '🔴 down'} (Last checked: {last_checked})\n"
    await message.reply(msg)

# Send downtime notification
async def send_downtime_notification(chat_id, friendly_name, url):
    msg = f"🚨 {friendly_name} ({url}) is back up! 🚨"
    await app.send_message(chat_id, msg)


# keep_alive function to keep the bot alive
async def keep_alive():
    while True:
        async with aiohttp.ClientSession() as session:
            # Keep sending requests until a 200 status is received
            while True:
                try:
                    app_url = f"{APP_URL}/status"
                    async with session.get(app_url) as response:
                        if response.status == 200:
                            break
                except:
                    pass
                await asyncio.sleep(10)  # Try every 10 seconds until successful
            await asyncio.sleep(600)  # Wait 10 minutes before the next keep-alive attempt

@web_app.route("/", methods=["GET"])            
async def home():
    return "<h1>Uptime Monitoring Bot is up and running!</h1>"

@web_app.route("/status", methods=["GET"])
async def bot_status():
    return jsonify({"status": "Alive", "timestamp": datetime.datetime.utcnow().isoformat()})

async def run_web_app():
    await web_app.run_task(host="0.0.0.0", port=8080)


# Start the bot and web app
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(monitor_websites())
    loop.create_task(run_web_app())
    loop.create_task(keep_alive())
    app.run()