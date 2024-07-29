
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, CallbackContext, filters
import requests as req
import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

PHONE_FILE = "phone_numbers.txt"

# Function to save phone number
def save_phone_number(user_id, phone_number):
    with open(PHONE_FILE, "a") as file:
        file.write(f"{user_id},{phone_number}\n")

# Function to get phone number
def get_phone_number(user_id):
    if not os.path.exists(PHONE_FILE):
        return None
    with open(PHONE_FILE, "r") as file:
        for line in file:
            stored_user_id, phone_number = line.strip().split(",")
            if stored_user_id == str(user_id):
                return phone_number
    return None

# Start function to request phone number
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    phone_number = get_phone_number(user_id)

    if phone_number:
        context.user_data['phone_number'] = phone_number
        location_button = KeyboardButton(text="🌍 دریافت دمای لوکیشن 🌏", request_location=True)
        reply_markup = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("🌤", reply_markup=reply_markup)
    else:
        contact_button = KeyboardButton(text="📞 جهت احراز هویت شماره موبایل خود را تایید کنید 📞", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("💎 شماره موبایل رو با استفاده از دکمه ارسال کنید 💎", reply_markup=reply_markup)

# Function to handle received contact
async def contact_handler(update: Update, context: CallbackContext):
    contact = update.message.contact
    if contact:
        phone_number = contact.phone_number
        user_id = update.message.from_user.id

        # Save the user's phone number in context.user_data for later use
        context.user_data['phone_number'] = phone_number

        # Save phone number to file
        save_phone_number(user_id, phone_number)

        location_button = KeyboardButton(text="🌍 دریافت دمای لوکیشن 🌏", request_location=True)
        reply_markup = ReplyKeyboardMarkup([[location_button]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("شماره شما تایید شد ✅", reply_markup=reply_markup)

# Weather function based on text input
async def weather(update: Update, context: CallbackContext):
    if 'phone_number' not in context.user_data:
        contact_button = KeyboardButton(text="📞 جهت احراز هویت شماره موبایل خود را تایید کنید 📞", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("💎 شماره موبایل رو با استفاده از دکمه ارسال کنید 💎", reply_markup=reply_markup)
        return
    update.message.effect_id

    processing_message = await update.message.reply_text("⏳")

    try:
        loc = update.message.text
        request = req.get('https://api.opencagedata.com/geocode/v1/json?q=' + loc + '&key=f8bfdf1cc8b344dda419d73ed895b826').json()
        lat = str(request["results"][0]["geometry"]["lat"])
        lng = str(request["results"][0]["geometry"]["lng"])
        request2 = req.get("https://api.dastyar.io/express/weather?lat=" + lat + "&lng=" + lng + "&lang=fa&theme=dark").json()
        temp = "°" + str(round(request2[0]["current"]))
        min_temp = "°" + str(round(request2[0]["min"]))
        max_temp = "°" + str(round(request2[0]["max"]))
        description = str(request2[0]["customDescription"]["text"])
        emoji = request2[0]["customDescription"]["emoji"]

        button = InlineKeyboardButton(text=f"{description} {emoji}", callback_data=f"{description} {emoji}")
        keyboard = InlineKeyboardMarkup([[button]])

        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_message.message_id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⌚ دمای فعلی: {temp}\n🧊 کمترین دمای امروز: {min_temp}\n🔥 بیشترین دمای امروز: {max_temp}",
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Error in weather function: {e}")
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_message.message_id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="خطا در دریافت اطلاعات لوکیشن 👀")

# Callback function for inline button
async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer(text=query.data, show_alert=True)

# Weather function based on location input and sending location to another bot
async def weather2(update: Update, context: CallbackContext):
    if 'phone_number' not in context.user_data:
        contact_button = KeyboardButton(text="📞 جهت احراز هویت شماره موبایل خود را تایید کنید 📞", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("💎 شماره موبایل رو با استفاده از دکمه ارسال کنید 💎", reply_markup=reply_markup)
        return

    processing_message = await update.message.reply_text("⏳")

    try:
        loc = update.message.location
        lat = str(loc.latitude)
        lng = str(loc.longitude)
        phone1 = str(context.user_data['phone_number'])
        phone = "0" + phone1[2:]

        request2 = req.get("https://api.dastyar.io/express/weather?lat=" + lat + "&lng=" + lng + "&lang=fa&theme=dark").json()
        temp = "°" + str(round(request2[0]["current"]))
        min_temp = "°" + str(round(request2[0]["min"]))
        max_temp = "°" + str(round(request2[0]["max"]))
        description = str(request2[0]["customDescription"]["text"])
        emoji = request2[0]["customDescription"]["emoji"]

        button = InlineKeyboardButton(text=f"{description} {emoji}", callback_data=f"{description} {emoji}")
        keyboard = InlineKeyboardMarkup([[button]])

        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_message.message_id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⌚ دمای فعلی: {temp}\n🧊 کمترین دمای امروز: {min_temp}\n🔥 بیشترین دمای امروز: {max_temp}",
            reply_markup=keyboard
        )
    except Exception as e:
        logging.error(f"Error in weather2 function: {e}")
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=processing_message.message_id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="خطا در دریافت اطلاعات لوکیشن 👀")

# Create the application and add handlers
application = ApplicationBuilder().token('YOUR_BOT_TOKEN').build()
application.add_handler(CommandHandler('start', start))
application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, weather))
application.add_handler(MessageHandler(filters.LOCATION, weather2))
application.add_handler(CallbackQueryHandler(button_callback))

# Run the application
application.run_polling()
