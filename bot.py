import datetime
import pytz
import asyncio
import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters, enums
from quart import Quart, jsonify
import os

# Configuration
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URI = os.getenv("DB_URI")
DB_NAME = os.getenv("DB_NAME", "uptimerobot")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "website")
MAX_WEBSITES_PER_USER = int(os.getenv("MAX_WEBSITES_PER_USER", 10))
APP_URL = os.getenv("APP_URL")
ADMINS = [int(admin_id) for admin_id in os.getenv("ADMINS", "").split(",") if admin_id.isdigit()]
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

# Initialize
app = Client("uptimebot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db_client = AsyncIOMotorClient(DB_URI)
db = db_client[DB_NAME]
collection = db[COLLECTION_NAME]

# Quart app initialization
web_app = Quart(__name__)


# Kolkata Timezone
kolkata_timezone = pytz.timezone(TIMEZONE)

# Function to check if a website is up or down
async def check_website(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                return response.status == 200
        except:
            return False

# Update the monitor_websites function to send requests according to the interval
async def monitor_websites():
    while True:
        cursor = collection.find({})
        async for document in cursor:
            current_time = datetime.datetime.now(tz=kolkata_timezone)
            current_time_aware = current_time.replace(tzinfo=kolkata_timezone)  # Make current_time timezone-aware
            if (current_time_aware - document["last_checked"]).total_seconds() >= document["interval"]:
                status = await check_website(document["url"])
                if status != document["status"]:
                    status_text = "down" if status else "up"
                    friendly_name = f'<a href="{document["url"]}">{document["friendly_name"]}</a>'
                    if status_text == "down":
                        msg = f"🚨 {friendly_name} is {status_text} 🚨"
                        await app.send_message(document["chat_id"], msg, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                    await collection.update_one(
                        {"url": document["url"], "chat_id": document["chat_id"]},
                        {"$set": {"status": status, "last_checked": current_time_aware}}
                    )
                # Ping the website based on the interval
                await check_website(document["url"])  # Send a request to the website
                
            await asyncio.sleep(30)  # Sleep for 30 seconds before the next iteration


# Start command
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    await message.reply(
        "Welcome to the Uptime Monitoring Bot! 🌐\n\n"
        "This bot monitors websites and notifies you of their status.\n"
        "Use /help to see available commands."
    )

# Help command
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

# Update command to update all website statuses
@app.on_message(filters.command("update") & filters.private)
async def update_command(client, message):
    cursor = collection.find({"chat_id": message.chat.id})
    async for document in cursor:
        status = await check_website(document["url"])
        await collection.update_one(
            {"url": document["url"], "chat_id": document["chat_id"]},
            {"$set": {"status": status, "last_checked": datetime.datetime.now(tz=kolkata_timezone)}}
        )
    await message.reply("All website statuses updated!")

# Add website command
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
            "last_checked": datetime.datetime.utcnow(),
            })

        link = f'<a href="{url}">{friendly_name}</a>'
        await message.reply(f"Added {link} to monitoring list with interval {interval//60} minutes.", parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        await message.reply(f"Usage: <code>/add website_url interval_in_minutes friendly_name</code>\n\n")

# Remove website command
@app.on_message(filters.command("remove") & filters.private)
async def remove_website(client, message):
    try:
        url = message.text.split()[1]
        result = await collection.delete_one({"url": url, "chat_id": message.chat.id})

        if result.deleted_count == 1:
            await message.reply(f"Removed {url} from monitoring list.")
        else:
            await message.reply(f"Could not find website with URL: {url}")
    except IndexError:
        await message.reply("Usage: `/remove <website_url>`")
    except Exception as e:
        await message.reply(f"An error occurred while removing the website: {str(e)}")

# Status command
@app.on_message(filters.command("status") & filters.private)
async def show_status(client, message):
    cursor = collection.find({"chat_id": message.chat.id})
    msg = f"🌐 Websites Status:\n\n"
    async for document in cursor:
        last_checked = document["last_checked"].strftime('%Y-%m-%d %H:%M:%S')
        status_icon = "🟢" if document['status'] else "🔴"
        friendly_name = document['friendly_name']
        status_text = "up" if document['status'] else "down"
        
        link = f'[{friendly_name}]({document["url"]})'
        msg += f"{status_icon} {link} ({status_text}) (Last checked: {last_checked})\n"
    
    await message.reply(msg, parse_mode=enums.ParseMode.MARKDOWN, disable_web_page_preview=True)


# keep_alive function to keep the bot alive
async def keep_alive():
    while True:
        async with aiohttp.ClientSession() as session:
            # Keep sending requests until a 200 status is received
            while True:
                try:
                    app_url = APP_URL
                    async with session.get(app_url) as response:
                        if response.status == 200:
                            break
                except:
                    pass
                await asyncio.sleep(10)  # Try every 10 seconds until successful
            await asyncio.sleep(600)  # Wait 10 minutes before the next keep-alive attempt

# Web app routes & home page
@web_app.route("/", methods=["GET"])            
async def home():
    return jsonify({"status": "Alive", "timestamp": datetime.datetime.utcnow().isoformat()})

# Run the web app
async def run_web_app():
    await web_app.run_task(host="0.0.0.0", port=8080)

# Start the bot and web app
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(monitor_websites())
    loop.create_task(run_web_app())
    loop.create_task(keep_alive())
    app.run()
