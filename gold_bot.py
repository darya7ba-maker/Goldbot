1import requests
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

