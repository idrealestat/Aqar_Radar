FROM python:3.11-slim

# تثبيت dependencies المطلوبة لتشغيل Playwright
RUN apt-get update -q && \
    apt-get install -y -qq --no-install-recommends \
    xvfb \
    libxcomposite1 \
    libxdamage1 \
    libatk1.0-0 \
    libasound2 \
    libdbus-1-3 \
    libnspr4 \
    libgbm1 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libnss3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# تثبيت متصفح Chromium الخاص بـ Playwright
RUN playwright install chromium

# نسخ ملفات البوت
COPY bot.py .
COPY scraper.py .

# متغير البيئة لتحديد مسار متصفح Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.cache/playwright

# تشغيل البوت
CMD ["python", "bot.py"]
