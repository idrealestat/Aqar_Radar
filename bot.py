import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# استيراد دوال السكريبت من scraper.py
from scraper import fetch_all_platforms, analyze_with_gemini

# ======================= إعداد المتغيرات =======================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ تأكد من وجود TELEGRAM_BOT_TOKEN و GEMINI_API_KEY في متغيرات البيئة")

# إعداد Gemini
genai.configure(api_key=GEMINI_API_KEY)

# إعداد التسجيل
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================= دوال البوت =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الرسالة الترحيبية عند بدء المحادثة"""
    welcome_msg = """
🏠 **مرحباً بك في الباحث العقاري الذكي!**

اختر ما تريد القيام به:

1️⃣ **عرض** - لدي عقار وأريد نشره للبيع أو الإيجار (سأبحث عن **طلبات** المشترين/المستأجرين المطابقة لعقاري).
2️⃣ **طلب** - أنا أبحث عن عقار للشراء أو الإيجار (سأبحث عن **عروض** البائعين/المؤجرين المطابقة لطلبي).
3️⃣ **توفير مطابقة متكاملة** - أريد أن تريني **جميع العروض وجميع الطلبات** الموجودة في المواقع العقارية والتي تتطابق مع المواصفات التي سأرسلها.

فضلاً اختر رقم الخيار (1، 2، أو 3) ثم أرسل التفاصيل المطلوبة.
أنا في انتظارك 👇
"""
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة رسائل المستخدم وتشغيل البحث"""
    user_message = update.message.text.strip()
    user_id = update.effective_user.id
    
    # إرسال إشعار "جاري الكتابة"
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # 1. تشغيل السكريبت لجلب البيانات من المواقع
    await update.message.reply_text("🔍 جاري البحث في المواقع العقارية... قد يستغرق هذا دقيقة.")
    
    try:
        raw_data = await fetch_all_platforms()
        logger.info(f"✅ تم جمع البيانات من {len(raw_data)} مصدر")
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء جلب البيانات: {e}")
        return
    
    # 2. تمرير البيانات إلى Gemini للتحليل
    await update.message.reply_text("🧠 جاري تحليل البيانات وتصفيتها...")
    
    try:
        analysis_result = analyze_with_gemini(raw_data, user_message)
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء التحليل: {e}")
        return
    
    # 3. إرسال النتيجة
    await update.message.reply_text(analysis_result, parse_mode="Markdown")
    
    # 4. التذييل
    footer = """
---
هل لديك طلب بحث آخر؟
- عرض
- طلب
- توفير مطابقة متكاملة (عرض + طلب)
"""
    await update.message.reply_text(footer)

# ======================= التشغيل =======================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("✅ البوت العقاري يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
