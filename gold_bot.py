import requests
from bs4 import BeautifulSoup
import time
import datetime
import json

# ─── تنظیمات ───────────────────────────────────────────────
BOT_TOKEN = "8688348591:AAG5eWT695RyNg3r05AiHWLcAAVma16OcBM"
CHANNEL_ID = "-1003773309751"
CHECK_INTERVAL = 30  # ثانیه
START_HOUR = 11
START_MINUTE = 30
END_HOUR = 20
END_MINUTE = 0

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ─── آدرس‌های API سایت tgju ────────────────────────────────
PRICE_SOURCES = {
    "gold18":       "https://www.tgju.org/profile/geram18",
    "gold_bubble":  "https://www.tgju.org/profile/gold-coin-bubble-18",
    "coin_full":    "https://www.tgju.org/profile/sekee",
    "coin_half":    "https://www.tgju.org/profile/nim-sekee",
    "coin_quarter": "https://www.tgju.org/profile/rob-sekee",
    "coin_bubble":  "https://www.tgju.org/profile/gold-coin-bubble",
    "tether":       "https://www.tgju.org/profile/tether",
    "dollar":       "https://www.tgju.org/profile/price_dollar_rl",
    "bitcoin_usd":  "https://www.tgju.org/profile/bitcoin",
    "bitcoin_irr":  "https://www.tgju.org/profile/bitcoin-irt",
    "fund_ayar":    "https://www.tgju.org/profile/ayar-gold-fund",
    "fund_derakhshan": "https://www.tgju.org/profile/derakhshan-gold-fund",
}

LABELS = {
    "gold18":           "طلای ۱۸ عیار",
    "gold_bubble":      "حباب طلا ۱۸ عیار",
    "coin_full":        "سکه تمام بهار آزادی",
    "coin_half":        "نیم سکه امامی",
    "coin_quarter":     "ربع سکه",
    "coin_bubble":      "حباب سکه",
    "tether":           "تتر (USDT)",
    "dollar":           "دلار",
    "bitcoin_usd":      "بیتکوین (دلار)",
    "bitcoin_irr":      "بیتکوین (تومان)",
    "fund_ayar":        "صندوق عیار",
    "fund_derakhshan":  "صندوق درخشان",
}

UNITS = {
    "gold18":           "تومان",
    "gold_bubble":      "تومان",
    "coin_full":        "تومان",
    "coin_half":        "تومان",
    "coin_quarter":     "تومان",
    "coin_bubble":      "تومان",
    "tether":           "تومان",
    "dollar":           "ریال",
    "bitcoin_usd":      "دلار",
    "bitcoin_irr":      "تومان",
    "fund_ayar":        "تومان",
    "fund_derakhshan":  "تومان",
}

# ذخیره قیمت‌های قبلی
previous_prices = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "fa,en;q=0.9",
}

def fetch_price(key):
    """دریافت قیمت از سایت tgju"""
    url = PRICE_SOURCES[key]
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # روش ۱: تگ span با کلاس مخصوص قیمت
        tag = soup.select_one("span.info-price")
        if tag:
            return clean_price(tag.get_text())

        # روش ۲: تگ با data-col="info.last_trade.PDrCotVal"
        tag = soup.select_one('[data-col="info.last_trade.PDrCotVal"]')
        if tag:
            return clean_price(tag.get_text())

        # روش ۳: جستجوی عمومی در جدول قیمت
        tag = soup.select_one("td.text-left strong")
        if tag:
            return clean_price(tag.get_text())

        # روش ۴: meta og:description
        meta = soup.find("meta", property="og:description")
        if meta and meta.get("content"):
            import re
            nums = re.findall(r"[\d,]+", meta["content"])
            if nums:
                return clean_price(nums[0])

        return None
    except Exception as e:
        print(f"[ERROR] fetch_price({key}): {e}")
        return None


def clean_price(text):
    """پاک‌سازی متن قیمت"""
    text = text.strip().replace("\u200c", "").replace("\n", "").replace(" ", "")
    # فقط اعداد و کاما باقی بمونه
    import re
    text = re.sub(r"[^\d,]", "", text)
    return text if text else None


def format_number(price_str):
    """فرمت‌بندی عدد با جداکننده هزار"""
    try:
        num = int(price_str.replace(",", ""))
        return f"{num:,}"
    except:
        return price_str


def send_telegram_message(text):
    """ارسال پیام به کانال تلگرام"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        data = r.json()
        if not data.get("ok"):
            print(f"[TELEGRAM ERROR] {data}")
        return data.get("ok", False)
    except Exception as e:
        print(f"[TELEGRAM EXCEPTION] {e}")
        return False


def is_working_hours():
    """بررسی ساعت کاری"""
    now = datetime.datetime.now()
    start = now.replace(hour=START_HOUR, minute=START_MINUTE, second=0, microsecond=0)
    end = now.replace(hour=END_HOUR, minute=END_MINUTE, second=0, microsecond=0)
    return start <= now <= end


def build_message(prices, prev_prices):
    """ساخت پیام نهایی"""
    now = datetime.datetime.now().strftime("%H:%M:%S  |  %Y/%m/%d")
    lines = [f"📊 <b>بروزرسانی قیمت‌ها</b>\n🕐 {now}\n"]

    sections = [
        ("🥇 طلا", ["gold18", "gold_bubble"]),
        ("🪙 سکه", ["coin_full", "coin_half", "coin_quarter", "coin_bubble"]),
        ("💵 ارز", ["tether", "dollar"]),
        ("₿ بیتکوین", ["bitcoin_usd", "bitcoin_irr"]),
        ("📈 صندوق‌های طلا", ["fund_ayar", "fund_derakhshan"]),
    ]

    for section_title, keys in sections:
        lines.append(f"\n{section_title}")
        for key in keys:
            label = LABELS[key]
            unit = UNITS[key]
            price = prices.get(key)
            prev = prev_prices.get(key)

            if price is None:
                lines.append(f"  • {label}: ─")
                continue

            # تعیین جهت تغییر
            try:
                p_num = int(price.replace(",", ""))
                arrow = ""
                if prev:
                    prev_num = int(prev.replace(",", ""))
                    if p_num > prev_num:
                        arrow = " 🔺"
                    elif p_num < prev_num:
                        arrow = " 🔻"
            except:
                arrow = ""

            formatted = format_number(price)
            lines.append(f"  • {label}: <b>{formatted}</b> {unit}{arrow}")

    lines.append(f"\n🔗 <a href='https://www.tgju.org'>tgju.org</a>")
    return "\n".join(lines)


def fetch_all_prices():
    """دریافت همه قیمت‌ها"""
    prices = {}
    for key in PRICE_SOURCES:
        price = fetch_price(key)
        prices[key] = price
        time.sleep(0.3)  # تأخیر کوچک بین درخواست‌ها
    return prices


def main():
    global previous_prices
    print("🤖 ربات طلا شروع به کار کرد...")
    send_telegram_message("🤖 <b>ربات قیمت طلا فعال شد</b>\nهر ۳۰ ثانیه قیمت‌ها بروز می‌شوند.")

    last_send_time = 0

    while True:
        now = datetime.datetime.now()

        if not is_working_hours():
            # بررسی هر ۶۰ ثانیه برای شروع ساعت کاری
            next_check = 60
            print(f"[{now.strftime('%H:%M:%S')}] خارج از ساعت کاری. بعداً بررسی می‌شود...")
            time.sleep(next_check)
            continue

        current_time = time.time()
        if current_time - last_send_time < CHECK_INTERVAL:
            time.sleep(1)
            continue

        print(f"[{now.strftime('%H:%M:%S')}] در حال دریافت قیمت‌ها...")
        prices = fetch_all_prices()

        # بررسی اینکه آیا حداقل یه قیمت دریافت شده
        valid_prices = {k: v for k, v in prices.items() if v is not None}
        if not valid_prices:
            print("[WARNING] هیچ قیمتی دریافت نشد!")
            time.sleep(10)
            continue

        message = build_message(prices, previous_prices)
        success = send_telegram_message(message)

        if success:
            print(f"[{now.strftime('%H:%M:%S')}] ✅ پیام ارسال شد ({len(valid_prices)}/{len(PRICE_SOURCES)} قیمت)")
            previous_prices = {k: v for k, v in prices.items() if v is not None}
        else:
            print(f"[{now.strftime('%H:%M:%S')}] ❌ خطا در ارسال پیام")

        last_send_time = time.time()
        time.sleep(1)


if __name__ == "__main__":
    main()


