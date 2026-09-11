import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from deep_translator import GoogleTranslator

# ================== ตั้งค่า ==================
TOKEN = os.getenv("DISCORD_TOKEN")                    # ← ใส่ Bot Token ตรงนี้
CHANNEL_ID = 1547596723034132620               # ช่องที่คุณให้มา
SEEN_FILE = "seen_links.json"

# คำสำคัญสำหรับกรองข่าว
KEYWORDS = [
    # ================== BL ==================
    "BL",
    "ボーイズラブ",
    "ボーイズ・ラブ",
    # ================== การดัดแปลง / ละคร BL ==================
    "実写化",
    "ドラマ化",
    "実写ドラマ",
    # ================== นักแสดง ==================
    # 美しい彼
    "萩原利久",
    "八木勇征",
    # みなと商事コインランドリー
    "草川拓弥",
    "西垣匠",
    # 25時、赤坂で
    "駒木根葵汰",
    "新原泰佑",
    # 飴色パラドックス
    "木村慧人",
    "山中柔太朗",
    # 40までにしたい10のこと
    "風間俊介",
    "庄司浩平",
    # BLドラマの主演になりました
    "阿部顕嵐",
    "阿久津仁愛",
    # นักแสดงที่มีผลงาน BL / ติดตามเพิ่มเติม
    "奥智哉",
    "杢代和人",
    "鈴木仁",
    "押田岳",
    "井内悠陽",
    "阿久根温世",
    "武田航平",
    "渋谷謙人",
    "福田歩汰",
    "相原一心",
    "佐藤新",
    "織山尚大",
    "高橋文哉",
    "金子隼也",
    "前田拳太郎",
    "柏木悠",
    "樋口幸平",
    "増子敦貴",
    "長谷川慎",
    "古屋呂敏",
    "小西詠斗",
    "元之介",
    "中川翼",
    "桜木雅哉",
    "古川雄輝",
    "長野凌大",
    # 原因は自分にある。
    "大倉空人",
    "小泉光咲",
    "桜木雅哉",
    "長野凌大",
    "武藤潤",
    "杢代和人",
    "吉澤要人",

    # 四坂亮翔
    "四坂亮翔",
]

# ================== ฟังก์ชันแปลภาษา ==================
def translate_to_thai(text: str) -> str:
    if not text:
        return ""
    try:
        text = text[:1200]
        return GoogleTranslator(source='ja', target='th').translate(text)
    except Exception as e:
        print("แปลภาษาผิดพลาด:", e)
        return "(แปลไม่สำเร็จ)"

# ================== จัดการลิงก์ที่เคยโพสต์ ==================
def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)

# ================== ดึงข่าว ==================
def get_news_from_modelpress():
    news = []

    try:
        url = "https://mdpr.jp/drama/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        res = requests.get(url, headers=headers, timeout=15)

        print(f"🌐 Modelpress status: {res.status_code}")
        print(f"📄 Modelpress HTML length: {len(res.text)}")

        soup = BeautifulSoup(res.text, "html.parser")

        # ดูลิงก์ที่หน้าเว็บส่งกลับมาจริง ๆ
        all_links = soup.select("a[href]")
        print(f"🔗 Modelpress all links: {len(all_links)}")

        for a_tag in all_links[:50]:
            title = a_tag.get_text(" ", strip=True)
            link = a_tag.get("href")

            if title and link:
                print(f"🔎 {title[:80]} | {link}")

        return news

    except Exception as e:
        print("modelpress error:", e)

    return news

def get_news_from_oricon():
    news = []
    try:
        url = "https://www.oricon.co.jp/news/"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")

        for item in soup.select("div.news-item, li, article")[:10]:
            a_tag = item.select_one("a")
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            link = a_tag.get("href")
            if not title or not link:
                continue
            if not link.startswith("http"):
                link = "https://www.oricon.co.jp" + link

            if not any(kw in title for kw in KEYWORDS):
                continue

            img = item.select_one("img")
            image = img.get("src") if img else None

            news.append({
                "title": title,
                "link": link,
                "image": image,
                "source": "oricon"
            })
    except Exception as e:
        print("oricon error:", e)
    return news

def get_news_from_yahoo():
    news = []
    try:
        url = "https://news.yahoo.co.jp/search?p=BL+ドラマ+OR+実写化+BL&ei=UTF-8"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")

        for item in soup.select("li, div.newsFeed_item")[:10]:
            a_tag = item.select_one("a")
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            link = a_tag.get("href")
            if not title or not link:
                continue

            if not any(kw in title for kw in KEYWORDS):
                continue

            img = item.select_one("img")
            image = img.get("src") if img else None

            news.append({
                "title": title,
                "link": link,
                "image": image,
                "source": "Yahoo News"
            })
    except Exception as e:
        print("yahoo error:", e)
    return news

def get_all_news():
    modelpress_news = get_news_from_modelpress()
    oricon_news = get_news_from_oricon()
    yahoo_news = get_news_from_yahoo()

    print(f"🔎 Modelpress: พบข่าวที่ผ่าน filter {len(modelpress_news)} ข่าว")
    print(f"🔎 ORICON: พบข่าวที่ผ่าน filter {len(oricon_news)} ข่าว")
    print(f"🔎 Yahoo: พบข่าวที่ผ่าน filter {len(yahoo_news)} ข่าว")

    all_news = []
    all_news.extend(modelpress_news)
    all_news.extend(oricon_news)
    all_news.extend(yahoo_news)

    print(f"📊 รวมทั้งหมด: {len(all_news)} ข่าว")

    return all_news

# ================== บอท Discord ==================
intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ บอทออนไลน์แล้ว: {client.user}")
    check_news.start()

@tasks.loop(minutes=60)
async def check_news():
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ หา channel ไม่เจอ")
        return

    seen = load_seen()
    news_list = get_all_news()
    new_count = 0

    for news in news_list:
        if news["link"] in seen:
            continue

        title_th = translate_to_thai(news["title"])

        embed = discord.Embed(
            title=news["title"][:250],
            url=news["link"],
            description=f"**แปลไทย:**\n{title_th}",
            color=0xFF69B4,
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"แหล่งข่าว: {news['source']} • BL News Bot")

        if news.get("image"):
            embed.set_image(url=news["image"])

        await channel.send(embed=embed)
        seen.add(news["link"])
        new_count += 1

    if new_count > 0:
        save_seen(seen)
        print(f"📢 โพสต์ข่าวใหม่ {new_count} ข่าว")
    else:
        print("ไม่มีข่าวใหม่ในรอบนี้")

@check_news.before_loop
async def before():
    await client.wait_until_ready()

client.run(TOKEN)
