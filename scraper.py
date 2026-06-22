import os
import asyncio
import random
import logging
from playwright.async_api import async_playwright
import google.generativeai as genai

logger = logging.getLogger(__name__)

# قائمة المنصات التي سيتم البحث فيها
PLATFORMS = [
    {"name": "عقار", "url": "https://sa.aqar.fm/شقق-للبيع/الخبر"},
    {"name": "حراج", "url": "https://haraj.com.sa/tags/شقق-للبيع-الخبر"},
    {"name": "بيوت", "url": "https://www.bayut.sa/للبيع/شقق/الخبر"},
    {"name": "زاهب", "url": "https://zaheb.com/شقق-للبيع/الخبر"},
    # يمكنك إضافة المزيد من المنصات هنا
]

async def fetch_platform_data(platform):
    """جلب البيانات من منصة واحدة باستخدام Playwright"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # تأخير عشوائي لتجنب الحظر
            await asyncio.sleep(random.uniform(1, 3))
            
            await page.goto(platform["url"], wait_until="networkidle", timeout=60000)
            
            content = await page.evaluate("() => document.body.innerText")
            links = await page.evaluate("""() => Array.from(document.querySelectorAll('a'))
                .map(a => ({text: a.innerText, href: a.href}))
                .filter(link => link.href && link.href.includes('/'))""")
            
            await browser.close()
            
            return {
                "source": platform["name"],
                "url": platform["url"],
                "content": content[:8000],  # تقطيع لتجنب تجاوز حد API
                "links": links[:50]
            }
    except Exception as e:
        logger.warning(f"⚠️ فشل في جلب {platform['name']}: {e}")
        return None

async def fetch_all_platforms():
    """جلب البيانات من جميع المنصات بالتزامن"""
    tasks = [fetch_platform_data(p) for p in PLATFORMS]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]

def analyze_with_gemini(raw_data, user_request):
    """
    تحليل البيانات المجمعة وتصفيتها حسب طلب المستخدم عبر Gemini API
    """
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # بناء النص المرسل إلى Gemini
    combined_text = ""
    for item in raw_data:
        combined_text += f"\n\n--- المصدر: {item['source']} ---\n"
        combined_text += item['content'][:3000]  # أخذ جزء من النص
    
    prompt = f"""
    أنت محلل بيانات عقاري دقيق. قم بتحليل البيانات التالية واستخراج العروض التي تطابق طلب المستخدم.
    
    **طلب المستخدم:**
    {user_request}
    
    **البيانات المجمعة من المنصات:**
    {combined_text[:40000]}
    
    **المطلوب منك بدقة:**
    1. استخرج جميع العروض التي تطابق شروط المستخدم (المدينة، الحي، السعر، المواصفات إن وجدت).
    2. لكل عرض مطابق، استخرج:
       - العنوان الكامل (إن وجد)
       - الرابط المباشر (إن وجد)
       - رقم التواصل (إن وجد)
       - المصدر
       - السعر (إن وجد)
       - المساحة (إن وجدت)
    3. رتب النتائج من الأحدث إلى الأقدم (حسب التاريخ إن وجد).
    4. إذا لم تجد أي عرض مطابق، اكتب: "لم أجد أي عرض مطابق في المواقع التي تم البحث فيها."
    5. إذا كانت بعض التفاصيل غير متوفرة، اكتب "غير متاح" أو "غير مذكور".
    6. لا تختلق أي بيانات غير موجودة.
    
    **صيغة المخرجات:**
    قم بعرض النتائج على شكل قائمة مرقمة مع تفاصيل كل عرض.
    """
    
    response = model.generate_content(prompt)
    return response.text