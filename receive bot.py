from telethon import TelegramClient, events, Button
import imagehash
from PIL import Image
import os
import time
import json
from datetime import datetime
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors.rpcerrorlist import UserNotParticipantError

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

ITEMS_PER_PAGE = 9 
join = 'join.json'
JOIN_LINKS_FILE = 'join_links.json'
ADMIN_FILE = 'admins.json'
USERS_FILE = 'users.json'
DB_FILE = 'hash_log.txt'
DB_UPDATE_FILE = 'db_update_time.txt'
STATE_FILE = 'bot_state.json'
BANNED_FILE = 'banned_users.json'
# ------------------- فایل ها -------------------
def load_json(file, default):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f)
admins = load_json(ADMIN_FILE, {
  "main_admins": [5524241740],
  "admins": [5524241740]
})
users = load_json(USERS_FILE, [])
state = load_json(STATE_FILE, {"enabled": True})
join = load_json(join, {"join": False})
update_mode = {}
#---------------ban def--------------------
def load_banned():
    if os.path.exists(BANNED_FILE):
        with open(BANNED_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if all(isinstance(item, int) for item in data):
                data = [{"id": item, "reason": "بدون دلیل مشخص", "ban": True} for item in data]
                save_banned(data)
            return data
    return []

def save_banned(banned):
    with open(BANNED_FILE, 'w', encoding='utf-8') as f:
        json.dump(banned, f, ensure_ascii=False, indent=2)

banned_users = load_banned()
def get_ban_entry(user_id):
    for user in banned_users:
        if isinstance(user, dict) and "id" in user:
            if user["id"] == user_id:
                return user
    return None
async def ban_user(user_id, reason):
    entry = get_ban_entry(user_id)
    if entry:
        entry["ban"] = True
        entry["reason"] = reason
    else:
        banned_users.append({"id": user_id, "reason": reason, "ban": True})
    save_banned(banned_users)

async def unban_user(user_id):
    entry = get_ban_entry(user_id)
    if entry:
        entry["ban"] = False
        save_banned(banned_users)
        

def is_user_banned(user_id):
    entry = get_ban_entry(user_id)
    return entry and entry.get("ban", False)
def is_user_banned(user_id):
    entry = get_ban_entry(user_id)
    return entry and entry.get("ban", False)
#÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷
def load_admins():
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, 'r') as f:
            return json.load(f)
    data = {"main_admins": [5524241740], "admins": [5524241740]}
    save_admins(data)
    return data

def save_admins(data):
    with open(ADMIN_FILE, 'w') as f:
        json.dump(data, f)

admins_data = load_admins()
main_admins = admins_data["main_admins"]
admins = admins_data["admins"]

#------------------join--------------------
def load_join_links():
    if os.path.exists(JOIN_LINKS_FILE):
        with open(JOIN_LINKS_FILE, 'r') as f:
            return json.load(f)
    return []
def load_join():
    if os.path.exists(join):
        with open(join, 'r') as f:
            return json.load(f)
    return []
def save_join_links(links):
    with open(JOIN_LINKS_FILE, 'w') as f:
        json.dump(links, f)

    
#---------------------------------------
async def is_user_joined(user_id):
    links = load_join_links()
    for link in links:
        try:
            parts = link.rstrip('/').split('/')
            username = parts[-1]
            entity = await client.get_entity(username)
            await client(GetParticipantRequest(entity, user_id))
        except UserNotParticipantError:
            return False
        except Exception as e:
            continue
    return True
#--------------------join client---------------------
@client.on(events.NewMessage(pattern=r'^/gp (.+)$'))
async def add_gp(event):
    if event.sender_id not in admins:
        return
    if not event.is_private:
        return
    link = event.pattern_match.group(1).strip()
    links = load_join_links()
    if link not in links:
        links.append(link)
        save_join_links(links)
        await event.reply("✅ لینک جوین اجباری اضافه شد.")
    else:
        await event.reply("⚠️ این لینک قبلاً اضافه شده است.")

@client.on(events.NewMessage(pattern=r'^/delgp (.+)$'))
async def del_gp(event):
    if event.sender_id not in admins:
        return
    if not event.is_private:
        return
    link = event.pattern_match.group(1).strip()
    links = load_join_links()
    if link in links:
        links.remove(link)
        save_join_links(links)
        await event.reply("✅ لینک جوین اجباری حذف شد.")
    else:
        await event.reply("⚠️ این لینک پیدا نشد.")

@client.on(events.NewMessage)
async def check_join(event):
    if not event.is_private:
        return
    if event.sender_id in admins:
        return  # ادمین‌ها آزاد 

    if event.message.message.startswith(('/gp', '/delgp')):
        return

    joined = await is_user_joined(event.sender_id)
    if not joined:
        join["join"] = False
        links = load_join_links()
        if not links:
            await event.reply("⚠️ لینک جوین اجباری ثبت نشده است.")
            return
        buttons = [Button.url(f"✅ عضویت در گروه {i+1}", link) for i, link in enumerate(links)]
        await event.reply("⚠️ برای استفاده از ربات، ابتدا در گروه‌های زیر عضو شوید:", buttons=buttons)
        return
    if joined:
        join["join"] = True
# ------------------- ابزار ها -------------------
async def get_phash(message):
    file_path = await client.download_media(message.photo, file='temp_image.jpg')
    with Image.open(file_path) as img:
        phash_val = str(imagehash.phash(img))
    os.remove(file_path)
    return phash_val

async def find_caption_by_photo(photo):
    target_phash = await get_phash(photo)
    if not os.path.exists(DB_FILE):
        return None

    with open(DB_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                phash_val, caption = line.strip().split('|||')
                if imagehash.hex_to_hash(phash_val) - imagehash.hex_to_hash(target_phash) <= 5:
                    trimmed_caption = caption[15:] if len(caption) > 15 else caption
                    first_part = trimmed_caption.split()[0]
                    return f"⭕ name: `/receive {first_part}` \n⚫full name: `/receive{trimmed_caption}`"
            except:
                continue
    return None
# ------------------- افزودن ادمین -------------------
@client.on(events.NewMessage(pattern=r'/ad (\d+)'))
async def add_admin(event):
    if event.sender_id not in main_admins:
        return

    new_admin = int(event.pattern_match.group(1))
    if new_admin not in admins:
        admins.append(new_admin)
        admins_data["admins"] = admins
        save_admins(admins_data)
        await event.reply(f"✅ {new_admin} به عنوان ادمین اضافه شد.")
    else:
        await event.reply("⚠️ این کاربر از قبل ادمین است.")
        
@client.on(events.NewMessage(pattern=r'/adop (\d+)'))
async def add_main_admin(event):
    if event.sender_id not in main_admins:
        return

    new_main_admin = int(event.pattern_match.group(1))
    if new_main_admin not in main_admins:
        main_admins.append(new_main_admin)
        if new_main_admin not in admins:
            admins.append(new_main_admin)
        admins_data["main_admins"] = main_admins
        admins_data["admins"] = admins
        save_admins(admins_data)
        await event.reply(f"✅ {new_main_admin} به عنوان مالک اضافه شد.")
    else:
        await event.reply("⚠️ این کاربر از قبل ادمین اصلی است.")
#----------------------بن کردن---------------------
@client.on(events.NewMessage(pattern=r'^/rban(?: (\d+))?(?: (.+))?$'))
async def rban_handler(event):
    if event.sender_id not in main_admins:
        return
    if event.is_reply and not event.pattern_match.group(1):
        reply_msg = await event.get_reply_message()
        user = await reply_msg.get_sender()
        if user:
            reason = event.pattern_match.group(2) or "بدون دلیل"
            await ban_user(user.id, reason)
            await event.reply(f"✅ کاربر {user.id} بن شد.\nدلیل: {reason}")
    else:
        user_id_str = event.pattern_match.group(1)
        reason = event.pattern_match.group(2) or "بدون دلیل"
        if user_id_str:
            try:
                user_id = int(user_id_str)
                await ban_user(user_id, reason)
                await event.reply(f"✅ کاربر {user_id} بن شد.\nدلیل: {reason}")
            except ValueError:
                await event.reply("❌ آیدی نامعتبر است.")

@client.on(events.NewMessage(pattern=r'^/runban$'))
async def runban_handler(event):
    if event.sender_id not in main_admins:
        return
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        user = await reply_msg.get_sender()
        if user:
            await unban_user(user.id)
            await event.reply(f"✅ کاربر {user.id} از بن خارج شد.")

@client.on(events.NewMessage(pattern=r'^/runban (\d+)$'))
async def ruban_handler(event):
    if event.sender_id not in main_admins:
        return
    user_id_str = event.pattern_match.group(1)
    try:
        user_id = int(user_id_str)
        await unban_user(user_id)
        await event.reply(f"✅ کاربر {user_id} از بن خارج شد.")
    except ValueError:
        await event.reply("❌ آیدی نامعتبر است.")

@client.on(events.NewMessage)
async def handle_messages(event):
    sender = await event.get_sender()
    if sender and is_user_banned(sender.id):
        return
# ------------------- حذف ادمین -------------------
@client.on(events.NewMessage(pattern=r'/delad (\d+)'))
async def remove_admin(event):
    if event.sender_id not in main_admins:
        return
    remove_id = int(event.pattern_match.group(1))
    if remove_id in admins:
        admins.remove(remove_id)
        admins_data["admins"] = admins
        save_admins(admins_data)
        await event.reply(f"✅ {remove_id} از لیست ادمین‌ها حذف شد.")
    else:
        await event.reply("⚠️ این کاربر ادمین نیست.")

@client.on(events.NewMessage(pattern=r'/delop (\d+)'))
async def remove_main_admin(event):
    if event.sender_id not in main_admins:
        if event.sender_id in admins:
            await event.reply("⛔ فقط ادمین اصلی می‌تواند ادمین اصلی حذف کند.")
        else:
            return
    remove_id = int(event.pattern_match.group(1))
    if remove_id in main_admins:
        if len(main_admins) == 1:
            await event.reply("⚠️ حداقل یک مالک باید باقی بماند.")
            return
        main_admins.remove(remove_id)
        admins_data["main_admins"] = main_admins
        save_admins(admins_data)
        await event.reply(f"✅ {remove_id} از لیست مالک حذف شد.")
    else:
        await event.reply("⚠️ این کاربر مالک نیست.")
# ------------------- پنل -------------------
@client.on(events.NewMessage(pattern='/panel'))
async def panel(event):
    if event.sender_id not in admins:
        return

    user_count = len(users)
    card_count = sum(1 for line in open(DB_FILE, encoding='utf-8') if line.strip()) if os.path.exists(DB_FILE) else 0
    last_update = open(DB_UPDATE_FILE).read().strip() if os.path.exists(DB_UPDATE_FILE) else "نامشخص"

    panel_text = (
        f"📊 <b>پنل مدیریت ربات</b>\n\n"
        f"👥 تعداد کاربران: <code>{user_count}</code>\n"
        f"🗂️ تعداد کارت های دیتابیس: <code>{card_count}</code>\n"
        f"⏰ آخرین آپدیت: <code>{last_update}</code>\n\n"
        f"🛠️ دستورات:\n"
        f"/ad افزودن ادمین ➖ آیدی عددی\n"
        f'/delad ➖ حذف ادمین\n'
        f"/update ➖ آپلود دیتابیس\n"
        f"/remove d ➖ حذف دیتابیس\n"
        f"/rban بن کردن ➖ آیدی عددی \n"
        f"/runban حذف بن ➖ آیدی عددی \n"
        f"/on ➖ روشن کردن بات\n"
        f"/off ➖ خاموش کردن بات\n"
        
    )
    await event.reply(panel_text, parse_mode='html')
# ------------------- مدیریت دیتابیس -------------------
@client.on(events.NewMessage(pattern='/update'))
async def update_db(event):
    if event.sender_id not in admins:
        return
    update_mode[event.sender_id] = True
@client.on(events.NewMessage(pattern='/cnncel'))
async def update_db(event):
    if event.sender_id not in admins:
        return
    await event.reply("کنسل شد")
    update_mode[event.sender_id] = False
@client.on(events.NewMessage(pattern='/remove d'))
async def remove_db(event):
    if event.sender_id not in admins:
        return
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        await event.reply("✅ دیتابیس پاک شد ")
    else:
        await event.reply("error")

# ------------------- روشن / خاموش -------------------
@client.on(events.NewMessage(pattern='/on'))
async def turn_on(event):
    if event.sender_id not in admins:
        return
    state["enabled"] = True
    save_json(STATE_FILE, state)
    await event.reply("bot on ✅")

@client.on(events.NewMessage(pattern='/off'))
async def turn_off(event):
    if event.sender_id not in admins:
        return
    state["enabled"] = False
    save_json(STATE_FILE, state)
    await event.reply("bot off 🚫 ")

# ------------------- قابلیت پاسخ به /rname در گروه -------------------
@client.on(events.NewMessage(pattern='/rname'))
async def rname_group(event):
    sender = await event.get_sender()
    if sender and is_user_banned(sender.id):
        entry = get_ban_entry(sender.id)
        try:
            None
        except:
            None
        return
    if not state.get("enabled", True):
        return
    if not event.is_reply:
        return
    
    reply_msg = await event.get_reply_message()
    if not reply_msg.photo:
        return

    status_msg = await event.reply("🔍...")
    caption = await find_caption_by_photo(reply_msg)
    if caption:
        await status_msg.edit(caption)
    else:
        await status_msg.edit("❌ عکس پیدا نشد")

# ------------------- مدیریت پیام های دریافتی -------------------
@client.on(events.NewMessage(incoming=True))
async def handle_all(event):
    # حالت آپلود دیتابیس
    sender = await event.get_sender()
    if update_mode.get(event.sender_id):
        if event.file and event.file.name == 'hash_log.txt':
            await client.download_media(event.message, file=DB_FILE)
            with open(DB_UPDATE_FILE, 'w') as f:
                f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            await event.reply("✅ دیتابیس آپدیت شد.")
            update_mode[event.sender_id] = False
        else:
            await event.respond("در انتظار فایل اپدیت \n لغو /cancel")
        return
    if sender and is_user_banned(sender.id):
    # اگر پیام در گپ است، نادیده بگیر
        if event.is_group or event.is_channel:
            return

        # اگر پیام در پیوی است، پیام بده
        entry = get_ban_entry(sender.id)
        reason = entry.get("reason", "بدون دلیل مشخص")
        try:
            await client.send_message(sender.id, f"⛔️ شما بن شده‌اید.\n📌 دلیل: {reason}")
        except:
            pass
        return
    # روشن بودن بات
    if not state.get("enabled", True):
        return
    if not join.get("join", True):
        return
    
    # ثبت کاربران
    if event.is_private and event.sender_id not in users:
        users.append(event.sender_id)
        save_json(USERS_FILE, users)

    # بررسی عکس در پیوی
    if event.is_private and event.photo:
        status_msg = await event.reply("🔍 در حال بررسی...")
        caption = await find_caption_by_photo(event.message)
        if caption:
            await status_msg.edit(caption)
        else:
            await status_msg.edit("❌ عکس یافت نشد.")

            return 
#--------------------banlist-------------------------
def format_duration(seconds):
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return ' '.join(parts) if parts else "0m"
@client.on(events.NewMessage(pattern=r'^/banlist$'))
async def banlist_handler(event):
    await send_banlist_page(event, page=0)

async def send_banlist_page(event, page):
    banned = [user for user in banned_users if user.get("ban", False)]
    if not banned:
        await event.reply("⚪ هیچ کاربری بن نشده است.")
        return

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_users = banned[start:end]

    buttons = []
    row = []
    for user in page_users:
        user_id = user.get("id")
        try:
            entity = await client.get_entity(user_id)
            name = entity.first_name or "None"
        except:
            name = str(user_id)
        row.append(Button.inline(name, data=f"banuser:{user_id}:{page}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(Button.inline("⬅️ صفحه قبل", data=f"banlist_page:{page-1}"))
    if end < len(banned):
        nav_buttons.append(Button.inline("➡️ صفحه بعد", data=f"banlist_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    await event.respond(
        f"📄 لیست کاربران بن شده (تعداد: {len(banned)})\n\nبرای مشاهده جزئیات، روی نام کلیک کنید.",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"banlist_page:")))
async def banlist_page_callback(event):
    page = int(event.data.decode().split(":")[1])
    await event.delete()
    await send_banlist_page(event, page)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"banuser:")))
async def banuser_detail_callback(event):
    _, user_id_str, page_str = event.data.decode().split(":")
    user_id = int(user_id_str)
    page = int(page_str)

    entry = get_ban_entry(user_id)
    if not entry:
        await event.answer("کاربر یافت نشد.", alert=True)
        return

    try:
        entity = await client.get_entity(user_id)
        name = entity.first_name or "بی‌نام"
    except:
        name = "نامشخص"

    reason = entry.get("reason", "نامشخص")
    ban_status = "✅ بن شده" if entry.get("ban", False) else "❌ آزاد"
    ban_time = entry.get("time", time.time())
    duration = format_duration(int(time.time() - ban_time))

    text = (
        f"👤 نام: {name}\n"
        f"🆔 آیدی عددی: {user_id}\n"
        f"🔒 وضعیت: {ban_status}\n"
        f"⏱️ مدت زمان: {duration}\n"
        f"📌 دلیل بن: {reason}"
    )

    buttons = [
        [Button.inline("✅ آزاد کردن", data=f"unbanuser:{user_id}:{page}")],
        [Button.inline("🔙 بازگشت", data=f"banlist_page:{page}")]
    ]

    await event.edit(text, buttons=buttons)

@client.on(events.CallbackQuery(data=lambda d: d.startswith(b"unbanuser:")))
async def unbanuser_callback(event):
    _, user_id_str, page_str = event.data.decode().split(":")
    user_id = int(user_id_str)
    page = int(page_str)

    entry = get_ban_entry(user_id)
    if entry:
        entry["ban"] = False
        save_banned(banned_users)
        await event.answer("✅ کاربر آزاد شد.", alert=True)
    else:
        await event.answer("کاربر یافت نشد.", alert=True)
    await event.delete()
    await send_banlist_page(event, page)

print("Bot is running...")
client.run_until_disconnected()