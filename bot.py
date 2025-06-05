import os
import logging
from dotenv import load_dotenv
from yt_dlp import YoutubeDL
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

user_languages = {}

translations = {
    "uz": {
        "start": "👋 Salom!\n\nBu — *Saver on YouTube* 📅\nSiz YouTube’dan video yoki audio fayllarni yuklab olish uchun yaratilgan oddiy, lekin qulay botdasiz.\n\n🎬 Foydalanish: YouTube havolasini yuboring — men yuklab beraman.\n\n❌ Faqat YouTube havolalari yuboring.\n\n❓ Muammo bo‘lsa, @Abdullayev774 ga yozing",
        "choose_lang": "🔊 Tilni tanlang:",
        "choose_type": "🔊 Fayl turini tanlang:",
        "ask_link": "🔗 Iltimos, YouTube havolasini yuboring.",
        "buttons": ["\ud83c\udfb5 Audio", "\ud83c\udfa5 Video"],
        "downloading": "🔄 Yuklanmoqda...",
        "downloaded_by": "\n\n🔗 @SaveronYoutuber_bot orqali yuklab olindi"
    },
    "ru": {
        "start": "👋 Привет!\n\nЭто — *Saver on YouTube* 📅\nЭто простой и удобный бот для скачивания YouTube видео или аудио.\n\n🎬 Просто отправьте ссылку.\n\n❌ Только YouTube ссылки.\n\n❓ Если есть вопросы: @Abdullayev774",
        "choose_lang": "🔊 Выберите язык:",
        "choose_type": "🔊 Выберите тип файла:",
        "ask_link": "🔗 Отправьте ссылку на YouTube.",
        "buttons": ["\ud83c\udfb5 Аудио", "\ud83c\udfa5 Видео"],
        "downloading": "🔄 Скачивание...",
        "downloaded_by": "\n\n🔗 Скачано через @SaveronYoutuber_bot"
    },
    "en": {
        "start": "👋 Hello!\n\nWelcome to *Saver on YouTube* 📅\nYou can download videos or audio from YouTube here easily.\n\n🎬 Just send the YouTube link.\n\n❌ Only YouTube links are supported.\n\n❓ Questions? Message @Abdullayev774",
        "choose_lang": "🔊 Please choose your language:",
        "choose_type": "🔊 Select the file type:",
        "ask_link": "🔗 Send the YouTube link:",
        "buttons": ["\ud83c\udfb5 Audio", "\ud83c\udfa5 Video"],
        "downloading": "🔄 Downloading...",
        "downloaded_by": "\n\n🔗 Downloaded via @SaveronYoutuber_bot"
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("O'zbekcha", callback_data='lang_uz'),
            InlineKeyboardButton("Русский", callback_data='lang_ru'),
            InlineKeyboardButton("English", callback_data='lang_en')
        ]
    ]
    await update.message.reply_text(
        "🔊 Tilni tanlang / Choose language / Выберите язык:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[-1]
    user_languages[query.from_user.id] = lang
    tr = translations[lang]
    await query.message.reply_text(tr['start'])
    await query.message.reply_text(tr['ask_link'])

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = user_languages.get(update.message.from_user.id, 'uz')
    tr = translations[lang]

    keyboard = [
        [
            InlineKeyboardButton(tr['buttons'][0], callback_data=f"audio|{update.message.text}"),
            InlineKeyboardButton(tr['buttons'][1], callback_data=f"video|{update.message.text}")
        ]
    ]
    await update.message.reply_text(tr['choose_type'], reply_markup=InlineKeyboardMarkup(keyboard))

async def download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = user_languages.get(user_id, 'uz')
    tr = translations[lang]

    type_, url = query.data.split('|')
    await query.message.reply_text(tr['downloading'])

    try:
        ydl_opts = {
            'format': 'bestaudio/best' if type_ == 'audio' else 'best[ext=mp4]/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if type_ == 'audio':
            audio_path = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            if os.path.exists(audio_path):
                await query.message.reply_audio(audio=open(audio_path, 'rb'), title=info['title'], caption=tr['downloaded_by'])
                os.remove(audio_path)
            else:
                await query.message.reply_audio(audio=open(filename, 'rb'), title=info['title'], caption=tr['downloaded_by'])
                os.remove(filename)
        else:
            await query.message.reply_video(video=open(filename, 'rb'), caption=info['title'] + tr['downloaded_by'])
            os.remove(filename)

    except Exception as e:
        await query.message.reply_text(f"❌ Xatolik: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(button_handler, pattern=r"^lang_"))
    app.add_handler(CallbackQueryHandler(download_handler, pattern=r"^(audio|video)\|"))
    print(" Bot ishga tushdi...")
    app.run_polling()
