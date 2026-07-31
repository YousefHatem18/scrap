from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import json
import os
from dotenv import load_dotenv
load_dotenv()

URL = "https://egy.voxcinemas.com/showtimes?c=city-centre-alexandria&m=spider-man-brand-new-day&d=20260802"

# ملف بنحفظ فيه آخر قايمة أيام شفناها، عشان نقدر نقارن بيها في المرة الجاية
KNOWN_DATES_FILE = "known_dates.json"

# بيتقروا من متغيرات البيئة (.env محليًا / Secrets على GitHub Actions)
# مش مكتوبين هنا نهائيًا عشان مايتسربوش تاني
sender_email = os.environ["SENDER_EMAIL"]
app_password = os.environ["APP_PASSWORD"]
receiver_email = os.environ["RECEIVER_EMAIL"]


def sendEmail(new_days: list[dict]):

    subject = "🎬 يوم جديد متاح للحجز"

    body = "تم فتح يوم جديد للحجز:\n\n"

    for day in new_days:
        body += f"📅 {day['label']} ({day['date']})\n"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)

    print("✅ Email Sent")


def load_known_dates() -> set:
    """يرجّع مجموعة الأيام (date codes) اللي اتحفظت من آخر تشغيل"""
    if not os.path.exists(KNOWN_DATES_FILE):
        return set()
    with open(KNOWN_DATES_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_known_dates(date_codes: set):
    """يحفظ الأيام الحالية عشان نقارن بيها في المرة الجاية"""
    with open(KNOWN_DATES_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(date_codes), f, ensure_ascii=False)


def get_available_dates(url: str) -> list[dict]:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    results = []
    try:
        driver.get(url)

        wait = WebDriverWait(driver, 20)

        all_days = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".viewport ol li")
            )
        )
        print(f"إجمالي عدد الأيام في الصفحة: {len(all_days)}")

        for day_li in all_days:
            link = day_li.find_elements(By.TAG_NAME, "a")
            span = day_li.find_elements(By.TAG_NAME, "span")

            if link:
                el = link[0]
                href = el.get_attribute("href")
                match = re.search(r"[?&]d=(\d{8})", href or "")
                date_code = match.group(1) if match else None
            else:
                el = span[0]
                href = url
                match = re.search(r"[?&]d=(\d{8})", url)
                date_code = match.group(1) if match else None

            label = el.text.strip()
            if not label:
                continue

            results.append({
                "label": label,
                "date": date_code,
                "url": href,
            })

    finally:
        driver.quit()

    return results


if __name__ == "__main__":
    available = get_available_dates(URL)
    print("الأيام المتاحة للحجز:")
    for d in available:
        print(f" - {d['label']}  ({d['date']})")

    current_date_codes = {d["date"] for d in available if d["date"]}
    known_date_codes = load_known_dates()

    new_date_codes = current_date_codes - known_date_codes

    if new_date_codes:
        new_days = [d for d in available if d["date"] in new_date_codes]
        print(f"\nفيه يوم/أيام جديدة ظهرت: {[d['label'] for d in new_days]}")
        sendEmail(new_days)
        save_known_dates(current_date_codes)
    else:
        print("\nمفيش أيام جديدة عن آخر مرة.")