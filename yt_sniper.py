#!/usr/bin/env python3
"""
YouTube Shorts, Faceless Video & High-CTR Thumbnails Sniper 24/7 ($0 / 0 Make Credits)
======================================================================================
Laser-focused global USD/EUR/GBP client hunter ONLY for:
  1) Faceless YouTube Shorts / TikTok / Reels Video Production (Quiz, Facts, Finance, Psychology,
     Mystery, AI, Cash Cow, Kinetic Captions, Motion Graphics) — just like @TwoPercentQuiz!
  2) High-CTR YouTube Video Thumbnails & Channel Packaging (1280x720 HD, A/B CTR hooks, Logo/Banner)

Sources scanned every 30 minutes (0 blocks, 0 paid APIs):
  - Reddit [HIRING] & [TASK] feeds via Arctic Shift API (CreatorServices, VideoEditingRequests,
    forhire, DesignJobs, slavelabour, hiring, YouTube_startups, NewTubers, PartneredYoutube)
  - Freelancer.com Official Active Projects API (YouTube, Video Editing, Shorts/Reels, Motion Graphics, Thumbnails)
  - Worldwide Remote Creator & Video Job Boards (WeWorkRemotely, Remotive, RemoteOK, Jobicy)

Zero-API Smart Pitch Engine: crafts tailored, high-converting English proposals embedding
the live Behance-style Google Drive Portfolio (with playable MP4 demos + 12 HD CTR Thumbnails)
and live @TwoPercentQuiz channel proof, sent straight to Telegram with 1-tap apply & DM buttons!
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
SEEN_FILE = SCRIPT_DIR / "seen_leads.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, application/xml, text/xml, */*;q=0.8",
}

# ===================== LIVE PORTFOLIO LINKS (BEHANCE VIDEO & THUMBNAILS) =====================
PORTFOLIO_YT_BEHANCE = "https://drive.google.com/drive/folders/14hyi6ywgKXb0MYTOwwJwK6rb1b4mh69V"
PORTFOLIO_YT_CHANNEL = "https://www.youtube.com/@TwoPercentQuiz"
PORTFOLIO_MP4_DEMOS  = "https://drive.google.com/drive/folders/1mCt__hlyiglSK4RGe_6jV7F2lZOlTNFJ"
PORTFOLIO_THUMBS_12  = "https://drive.google.com/drive/folders/1BALOCIAMYtd8QzM2s5I_jCapkSnNdiKq"

# ===================== SUBREDDITS & FILTERING =====================
# (subreddit, fetch_limit, is_task_sub)
REDDIT_SUBS = [
    ("CreatorServices",      45, False),
    ("VideoEditingRequests", 40, False),
    ("forhire",              45, False),
    ("DesignJobs",           40, False),
    ("slavelabour",          40, True),
    ("hiring",               35, False),
    ("YouTube_startups",     35, False),
    ("NewTubers",            35, False),
    ("PartneredYoutube",     30, False),
]

# Freelancer.com verified Video/YouTube/Shorts/Thumbnail Skill IDs
FREELANCER_VIDEO_IDS = [174, 69, 602, 126, 130, 279, 600, 1013]
FREELANCER_THUMB_IDS = [20, 32, 602, 284, 170]
GOOD_CURRENCIES = {"USD", "EUR", "GBP", "AUD", "CAD"}

# STRICT TARGET KEYWORDS — ONLY Video Shorts / Faceless / Quiz / Reels / TikTok / YouTube Thumbnails!
SHORTS_VIDEO_KEYWORDS = [
    "youtube shorts", "yt shorts", "shorts editor", "short form", "short-form",
    "faceless youtube", "faceless channel", "faceless video", "faceless shorts",
    "cash cow", "cashcow", "youtube automation", "quiz video", "quiz channel",
    "trivia video", "trivia shorts", "riddle video", "tiktok editor", "reels editor",
    "instagram reels", "vertical video", "viral shorts", "kinetic captions",
    "hormozi style", "magnatesmedia", "documentary editor", "youtube video editor",
    "yt video editor", "motion graphics", "retention editor", "youtube editor",
    "video editor for youtube", "tiktok video", "reels video", "ai video editor",
    "storytelling shorts", "dark psychology", "motivation shorts", "finance shorts",
]

THUMBNAIL_KEYWORDS = [
    "youtube thumbnail", "yt thumbnail", "thumbnail designer", "thumbnail artist",
    "thumbnails", "high ctr thumbnail", "ctr thumbnail", "clickbait thumbnail",
    "video thumbnail", "youtube banner", "channel banner", "channel art",
    "youtube branding", "mrbeast thumbnail", "thumbnail maker", "thumbnail editor",
    "youtube packaging", "ctr", "click through rate",
]

# Hard reject: zero [FOR HIRE], zero spam, zero non-video/non-thumbnail design (logos/books/web dev/NSFW)
HARD_REJECT = [
    "[for hire]", "[offer]", "for hire:", "for hire]", "my portfolio", "hire me",
    "commissions open", "i am a video editor", "i'm a video editor", "i am a thumbnail designer",
    "i'm a thumbnail designer", "looking for work", "looking for clients", "available for hire",
    "nsfw", "erotica", "fetish", "onlyfans", "porn", "lewd", "hentai", "adult content",
    "unpaid", "revshare", "revenue share", "for exposure", "no budget", "free work", "profit share",
    "wedding video", "real estate drone", "real estate video", "color grading feature film",
    "book cover", "coloring book", "kdp", "kindle", "t-shirt", "merch", "flyer", "brochure",
    "menu design", "business card", "wordpress", "shopify", "react", "next.js", "laravel",
    "flutter", "python developer", "full-stack", "blockchain", "solidity", "data entry",
    "virtual assistant", "cold caller", "appointment setter", "ugc creator", "kick stream",
    "clippers for my", "clippers", "video clippers", "paid per 1,000 views", "per 1000 views",
    "clipping", "homework", "essay", "exam", "voice actor only", "talent sourcer",
    "subscribe to a plan", "onboarding call", "register on the platform",
    "scriptwriter only", "script writer needed", "looking for a scriptwriter",
]

REMOTE_TITLE_INCLUDE = [
    "thumbnail", "youtube", "shorts", "short-form", "short form",
    "video editor", "reels", "tiktok", "motion designer", "motion graphics",
]

REMOTE_TITLE_REJECT = [
    "director", "vp ", "head of", "staff ", "principal ", "senior manager",
    "us only", "united states only", "us-based", "uk only", "canada only",
    "onsite", "on-site", "hybrid", "internship", "intern ", "software", "engineer",
]


# ===================== DEDUP STORAGE =====================
def load_seen() -> dict:
    if SEEN_FILE.exists():
        try:
            data = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception as e:
            print(f"[WARN] Could not load seen_leads.json: {e}")
    return {}


def save_seen(seen: dict):
    cutoff = time.time() - 30 * 86400
    pruned = {k: v for k, v in seen.items() if isinstance(v, (int, float)) and v >= cutoff}
    if len(pruned) > 2500:
        pruned = dict(sorted(pruned.items(), key=lambda kv: kv[1], reverse=True)[:2500])
    SEEN_FILE.write_text(json.dumps(pruned, indent=2, sort_keys=True), encoding="utf-8")


# ===================== HELPERS =====================
def clean_text(s: str, max_len: int = 1200) -> str:
    if not s:
        return ""
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"\s+", " ", s).strip()
    return s[:max_len]


def format_age(ts: float) -> str:
    mins = max(1, int((time.time() - ts) / 60))
    if mins < 60:
        return f"منذ {mins} دقيقة"
    hours = mins / 60
    if hours < 24:
        return f"منذ {hours:.1f} ساعة"
    return f"منذ {hours/24:.1f} يوم"


def extract_budget(text: str) -> tuple:
    m = re.search(
        r"([\$€£])\s*(\d{1,5})\+?(?:\s*(?:-|to|–|—)\s*[\$€£]?\s*(\d{1,5})\+?)?(?:\s*(?:/\s*(?:month|mo|hour|hr|week|wk|video|short|reel|thumbnail|thumb)|per\s+(?:month|hour|week|video|short|reel|thumbnail)))?",
        text,
        re.I,
    )
    if m:
        lo = int(m.group(2))
        hi = int(m.group(3)) if m.group(3) else None
        full = re.sub(r"\s+", " ", m.group(0)).strip()
        return full, (hi if hi else lo)
    m2 = re.search(r"\b(\d{2,5})\+?\s*(usd|eur|gbp|dollars?)\b", text, re.I)
    if m2:
        val = int(m2.group(1))
        return f"${val} {m2.group(2).upper()}", val
    return "", 0


def classify_lead(title: str, desc: str) -> tuple:
    """Returns (category, score_boost, matched_hits) or (None, 0, []) if not a strict YT Video/Thumbnail match."""
    blob = f"{title} {desc}".lower()
    if any(bad in blob for bad in HARD_REJECT):
        return None, 0, []

    vid_hits = [k for k in SHORTS_VIDEO_KEYWORDS if k in blob]
    thb_hits = [k for k in THUMBNAIL_KEYWORDS if k in blob]

    # Also catch "shorts" + ("youtube" or "video editor" or "channel") cleanly
    if not vid_hits and re.search(r"\bshorts\b", blob) and any(w in blob for w in ["youtube", "video editor", "channel", "editing"]):
        vid_hits.append("shorts")

    # Guard against generic "ctr" matching unrelated words (require word boundary for "ctr")
    if "ctr" in thb_hits and not re.search(r"\bctr\b", blob):
        thb_hits.remove("ctr")

    if not vid_hits and not thb_hits:
        return None, 0, []

    # Extra guard: if matched ONLY "motion graphics" without video/youtube/shorts/reels/tiktok/thumbnail context, verify
    if vid_hits == ["motion graphics"] and not thb_hits:
        if not any(w in blob for w in ["youtube", "shorts", "reels", "tiktok", "video", "channel", "creator", "faceless"]):
            return None, 0, []

    if vid_hits and thb_hits:
        return "combo_video_thumb", 22, vid_hits[:3] + thb_hits[:2]
    if vid_hits:
        # Huge priority boost for Quiz / Faceless / Shorts / Cash Cow / Automation channels!
        vip = any(k in blob for k in ["quiz", "trivia", "faceless", "cash cow", "youtube shorts", "yt shorts", "short-form", "short form", "youtube automation", "reels", "tiktok"])
        return "faceless_shorts", (24 if vip else 16), vid_hits[:4]
    return "yt_thumbnails", 20, thb_hits[:4]


CAT_LABELS_AR = {
    "combo_video_thumb": "🔥 باك كامل: فيديوهات Shorts + مصغّرات CTR",
    "faceless_shorts":   "🎬 فيديوهات Faceless / Shorts / Quiz / Reels",
    "yt_thumbnails":     "🖼️ مصغّرات يوتيوب High-CTR Thumbnails",
}


def score_lead(lead: dict) -> int:
    score = 52 + lead.get("cat_boost", 0)
    age_h = (time.time() - lead["created_utc"]) / 3600.0
    if age_h <= 2:
        score += 18
    elif age_h <= 6:
        score += 13
    elif age_h <= 18:
        score += 8
    elif age_h <= 48:
        score += 4

    bval = lead.get("budget_usd", 0)
    if bval >= 300:
        score += 14
    elif bval >= 100:
        score += 10
    elif bval >= 30:
        score += 6
    elif bval >= 10:
        score += 3

    blob = f"{lead['title']} {lead['desc']}".lower()
    if any(w in blob for w in ["long term", "long-term", "ongoing", "monthly", "retainer", "weekly", "daily", "30 videos", "bulk"]):
        score += 8
    if any(w in blob for w in ["quiz", "faceless", "cash cow", "high ctr", "ctr"]):
        score += 7

    return min(99, max(0, score))


# ===================== FETCHERS =====================
def is_hiring_reddit_post(title: str, body: str, sub: str, is_task_sub: bool) -> bool:
    tl = title.lower()
    bl = body.lower()
    # Never self-promo
    if any(x in tl for x in ["[for hire]", "[offer]", "for hire", "my commissions", "i will make", "i make thumbnails", "i edit videos"]):
        return False
    if is_task_sub:
        return "[task]" in tl
    if any(tag in tl for tag in ["[hiring]", "(hiring)", "hiring:", "hiring a ", "hiring an "]):
        return True
    # For YouTube creator subs (YouTube_startups, NewTubers, PartneredYoutube, VideoEditingRequests): strict hiring intent!
    hiring_phrases = [
        "looking for a thumbnail", "looking for thumbnail", "need a thumbnail", "need thumbnail",
        "looking for a video editor", "looking for video editor", "looking for a shorts editor",
        "looking for shorts editor", "need a shorts editor", "need a video editor",
        "hiring a shorts editor", "hiring a thumbnail", "hiring a video editor",
        "looking for an editor", "want to hire", "paying $", "budget is $", "paid gig",
        "looking for someone to edit", "looking for someone to make", "need someone to make",
    ]
    return any(p in tl or p in bl[:350] for p in hiring_phrases)


def fetch_reddit_leads(max_age_hours: float = 48.0) -> list:
    leads = []
    cutoff = time.time() - max_age_hours * 3600
    for sub, limit, is_task_sub in REDDIT_SUBS:
        url = f"https://arctic-shift.photon-reddit.com/api/posts/search?subreddit={sub}&limit={limit}&sort=desc"
        data = None
        for attempt in range(2):
            try:
                r = requests.get(url, headers=HEADERS, timeout=18)
                if r.status_code == 200:
                    data = r.json().get("data", [])
                    break
            except Exception as e:
                if attempt == 1:
                    print(f"[WARN] Reddit r/{sub} fetch error: {e}")
                time.sleep(1.2)
        if not data:
            continue

        for p in data:
            created = float(p.get("created_utc") or 0)
            if created < cutoff:
                continue
            title = clean_text(p.get("title", ""), 260)
            body = clean_text(p.get("selftext", ""), 1200)
            author = p.get("author", "")
            if not title or author in ("[deleted]", "AutoModerator", ""):
                continue
            if not is_hiring_reddit_post(title, body, sub, is_task_sub):
                continue

            cat, boost, hits = classify_lead(title, body)
            if not cat:
                continue

            b_str, b_usd = extract_budget(f"{title} {body}")
            post_id = p.get("id", "")
            permalink = p.get("permalink") or f"/r/{sub}/comments/{post_id}/"
            leads.append({
                "id": f"reddit:{post_id}",
                "source": f"Reddit r/{sub}",
                "platform": "reddit",
                "title": title,
                "desc": body[:500] or title,
                "url": f"https://www.reddit.com{permalink}",
                "dm_url": f"https://www.reddit.com/message/compose/?to={urllib.parse.quote(author)}&subject={urllib.parse.quote('Re: ' + title[:60])}",
                "author": f"u/{author}",
                "budget": b_str or "تحديد مع العميل ($)",
                "budget_usd": b_usd,
                "created_utc": created,
                "category": cat,
                "cat_boost": boost,
                "hits": hits,
            })
        time.sleep(0.25)
    return leads


def fetch_freelancer_leads(max_age_hours: float = 36.0) -> list:
    leads = []
    cutoff = time.time() - max_age_hours * 3600
    seen_ids = set()

    queries = [
        ("jobs[]", FREELANCER_VIDEO_IDS, "youtube shorts"),
        ("jobs[]", FREELANCER_VIDEO_IDS, "faceless video"),
        ("jobs[]", FREELANCER_VIDEO_IDS, "reels tiktok editor"),
        ("jobs[]", FREELANCER_THUMB_IDS, "youtube thumbnail"),
        ("jobs[]", FREELANCER_VIDEO_IDS, ""),
    ]
    for param_name, skill_ids, q_text in queries:
        params = [("limit", "30"), ("compact", "true"), ("full_description", "true")]
        for sid in skill_ids:
            params.append((param_name, str(sid)))
        if q_text:
            params.append(("query", q_text))
        try:
            r = requests.get(
                "https://www.freelancer.com/api/projects/0.1/projects/active/",
                params=params,
                headers=HEADERS,
                timeout=18,
            )
            if r.status_code != 200:
                continue
            projects = r.json().get("result", {}).get("projects", [])
        except Exception as e:
            print(f"[WARN] Freelancer API error ({q_text}): {e}")
            continue

        for pr in projects:
            pid = pr.get("id")
            if not pid or pid in seen_ids:
                continue
            seen_ids.add(pid)

            cur = (pr.get("currency") or {}).get("code", "")
            if cur not in GOOD_CURRENCIES:
                continue
            created = float(pr.get("time_submitted") or pr.get("submitdate") or 0)
            if created < cutoff:
                continue
            if pr.get("language") and pr.get("language") != "en":
                continue

            title = clean_text(pr.get("title", ""), 260)
            desc = clean_text(pr.get("description") or pr.get("preview_description") or "", 1000)
            cat, boost, hits = classify_lead(title, desc)
            if not cat:
                continue

            bobj = pr.get("budget") or {}
            bmin, bmax = bobj.get("minimum"), bobj.get("maximum")
            sym = (pr.get("currency") or {}).get("sign", "$")
            b_str = f"{sym}{int(bmin)}–{sym}{int(bmax)} {cur}" if (bmin and bmax) else f"{cur} Project"
            b_usd = int(bmax or bmin or 0)
            seo = pr.get("seo_url") or str(pid)
            leads.append({
                "id": f"fl:{pid}",
                "source": "Freelancer.com",
                "platform": "freelancer",
                "title": title,
                "desc": desc[:500] or title,
                "url": f"https://www.freelancer.com/projects/{seo}",
                "dm_url": "",
                "author": "Verified Freelancer Client",
                "budget": b_str,
                "budget_usd": b_usd,
                "created_utc": created,
                "category": cat,
                "cat_boost": boost,
                "hits": hits,
            })
        time.sleep(0.25)
    return leads


def fetch_remote_boards(max_age_hours: float = 72.0) -> list:
    leads = []
    cutoff = time.time() - max_age_hours * 3600

    # 1) Remotive (Design & Marketing / Media)
    for cat_slug in ("design", "marketing"):
        try:
            r = requests.get(f"https://remotive.com/api/remote-jobs?category={cat_slug}&limit=40", headers=HEADERS, timeout=16)
            if r.status_code == 200:
                for j in r.json().get("jobs", []):
                    title = clean_text(j.get("title", ""), 220)
                    tl = title.lower()
                    if not any(k in tl for k in REMOTE_TITLE_INCLUDE):
                        continue
                    if any(b in tl for b in REMOTE_TITLE_REJECT):
                        continue
                    try:
                        created = datetime.fromisoformat(j.get("publication_date", "").replace("Z", "+00:00")).timestamp()
                    except Exception:
                        created = time.time()
                    if created < cutoff:
                        continue
                    desc = clean_text(j.get("description", ""), 800)
                    cat, boost, hits = classify_lead(title, desc)
                    if not cat:
                        continue
                    leads.append({
                        "id": f"remotive:{j.get('id')}",
                        "source": "Remotive (Remote)",
                        "platform": "remote",
                        "title": f"{title} — {j.get('company_name', '')}",
                        "desc": desc[:420],
                        "url": j.get("url", ""),
                        "dm_url": "",
                        "author": j.get("company_name", "Remote Company"),
                        "budget": j.get("salary") or "Remote Paid Role ($)",
                        "budget_usd": 500,
                        "created_utc": created,
                        "category": cat,
                        "cat_boost": boost,
                        "hits": hits,
                    })
        except Exception:
            pass

    # 2) WeWorkRemotely Design RSS
    try:
        r = requests.get("https://weworkremotely.com/categories/remote-design-jobs.rss", headers=HEADERS, timeout=16)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            for item in root.findall(".//item")[:40]:
                title = clean_text(item.findtext("title", ""), 220)
                tl = title.lower()
                if not any(k in tl for k in REMOTE_TITLE_INCLUDE) or any(b in tl for b in REMOTE_TITLE_REJECT):
                    continue
                try:
                    created = parsedate_to_datetime(item.findtext("pubDate", "")).timestamp()
                except Exception:
                    created = time.time()
                if created < cutoff:
                    continue
                desc = clean_text(item.findtext("description", ""), 800)
                cat, boost, hits = classify_lead(title, desc)
                if not cat:
                    continue
                link = item.findtext("link", "").strip()
                leads.append({
                    "id": f"wwr:{abs(hash(link))}",
                    "source": "WeWorkRemotely",
                    "platform": "remote",
                    "title": title,
                    "desc": desc[:420],
                    "url": link,
                    "dm_url": "",
                    "author": "WWR Verified Employer",
                    "budget": "Remote Salary / Contract ($)",
                    "budget_usd": 500,
                    "created_utc": created,
                    "category": cat,
                    "cat_boost": boost,
                    "hits": hits,
                })
    except Exception:
        pass
    return leads


# ===================== SMART HIGH-CONVERTING ENGLISH PITCH ENGINE (0 API!) =====================
def build_smart_pitch(lead: dict) -> str:
    cat = lead["category"]
    tl = lead["title"].lower()

    if cat == "combo_video_thumb":
        return (
            "Hi! I saw you're looking for someone who handles both YouTube video/Shorts editing "
            "and high-CTR thumbnails — that's what I do daily.\n\n"
            "I edit vertical short-form videos across 8 styles (interactive quiz, split-screen Would You Rather, "
            "podcast clips, dark psychology, finance, true crime & tech — you can see my work live at "
            "youtube.com/@TwoPercentQuiz) alongside high-CTR 1280x720 thumbnails across 12 niches.\n\n"
            f"My Portfolio (4 Full HD MP4 Video Samples & 20 Thumbnails):\n{PORTFOLIO_YT_BEHANCE}\n\n"
            "Happy to jump on a quick trial video or thumbnail within 24–48h. Let me know what style you're aiming for!"
        )

    if cat == "faceless_shorts":
        style_note = "quiz/trivia Shorts with custom countdown graphics and pacing" if any(k in tl for k in ["quiz", "trivia", "riddle"]) else (
            "vertical Shorts/Reels with strong 3-second hooks, custom motion graphics, kinetic captions & clean SFX"
        )
        return (
            f"Hi! I saw your post and would love to edit your {style_note}.\n\n"
            "I edit short-form vertical videos built for strong watch-time and comments — you can check out "
            f"a live channel I edit for here: {PORTFOLIO_YT_CHANNEL} (90+ Shorts published), plus samples across "
            "Quiz, Would You Rather, Podcast Clips, Dark Psychology, Finance, True Crime & Tech.\n\n"
            f"My Portfolio + 4 Full 1080x1920 MP4 Video Samples:\n{PORTFOLIO_YT_BEHANCE}\n\n"
            "Available for single videos or weekly/monthly batches (24–48h turnaround). Happy to start with a quick trial edit!"
        )

    # yt_thumbnails
    niche_hint = "your exact niche"
    for kw, label in [
        ("finance", "Finance & Business"), ("business", "Finance & Business"), ("crypto", "Crypto & Finance"),
        ("health", "Health & Wellness"), ("tech", "Tech & AI"), ("ai", "Tech & AI"),
        ("documentary", "Documentary & Storytelling"), ("crime", "True Crime & Mystery"),
        ("podcast", "Podcasts & Interviews"), ("gaming", "Gaming"), ("minecraft", "Gaming"),
        ("fitness", "Fitness"), ("challenge", "Viral Challenges"),
        ("real estate", "Luxury & Real Estate"), ("sports", "Sports & Football"), ("football", "Sports & Football"),
        ("car", "Automotive & Supercars"), ("food", "Food & Cooking"), ("travel", "Travel & Vlogs"),
        ("psychology", "Psychology & Self-Improvement"),
    ]:
        if re.search(rf"\b{re.escape(kw)}\b", tl):
            niche_hint = label
            break

    return (
        f"Hi! Saw you're looking for a YouTube Thumbnail Designer — I design clean, high-CTR 1280x720 thumbnails "
        f"with strong lighting, clear focal points & short punchy hooks (including {niche_hint}).\n\n"
        f"My Portfolio (20 HD Thumbnail Samples + Before/After Makeovers):\n{PORTFOLIO_YT_BEHANCE}\n\n"
        "Fast 24h turnaround and open to A/B concept tweaks. "
        "Send me your next video title if you'd like to test one out!"
    )


# ===================== TELEGRAM ALERTS =====================
def send_telegram_lead(token: str, chat_id: str, lead: dict, pitch: str) -> bool:
    cat_lbl = CAT_LABELS_AR.get(lead["category"], "🎬 YouTube Video / Thumbnails")
    score = lead["score"]
    fire = "🔥🔥🔥" if score >= 85 else ("🔥🔥" if score >= 72 else "⚡")

    snippet = html.escape(lead["desc"][:280])
    if len(lead["desc"]) > 280:
        snippet += "..."

    msg = (
        f"{fire} <b>صيد جديد — {html.escape(cat_lbl)}</b>\n"
        f"⭐ <b>التقييم:</b> <code>{score}/100</code>  |  📍 <b>{html.escape(lead['source'])}</b>\n"
        f"💰 <b>الميزانية:</b> <code>{html.escape(lead['budget'])}</code>  |  ⏱️ {format_age(lead['created_utc'])}\n\n"
        f"📌 <b>{html.escape(lead['title'])}</b>\n"
        f"📝 <i>{snippet}</i>\n\n"
        f"✉️ <b>رسالة التقديم الجاهزة (اضغط للنسخ — مربوطة ببورتفوليو الفيديوهات والـ Thumbnails!):</b>\n"
        f"<pre>{html.escape(pitch)}</pre>"
    )

    buttons = [[{"text": "🚀 فتح المشروع والتقديم الآن", "url": lead["url"]}]]
    if lead.get("dm_url"):
        buttons[0].append({"text": "💬 مراسلة مباشرة (DM)", "url": lead["dm_url"]})
    buttons.append([{"text": "🎨 فتح البورتفوليو (Drive)", "url": PORTFOLIO_YT_BEHANCE}])

    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": json.dumps({"inline_keyboard": buttons}),
    }
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data=payload, timeout=20)
        if r.status_code == 200 and r.json().get("ok"):
            return True
        print(f"[ERR] Telegram failed: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"[ERR] Telegram exception: {e}")
    return False


# ===================== MAIN =====================
def main():
    ap = argparse.ArgumentParser(description="YouTube Shorts, Faceless Video & CTR Thumbnails Sniper 24/7")
    ap.add_argument("--dry-run", action="store_true", help="Print matches without sending to Telegram or saving seen")
    ap.add_argument("--max-alerts", type=int, default=5, help="Max Telegram alerts per run (default 5)")
    ap.add_argument("--min-score", type=int, default=62, help="Minimum lead score (default 62)")
    ap.add_argument("--hours", type=float, default=48.0, help="Lookback window in hours (default 48)")
    ap.add_argument("--ignore-seen", action="store_true", help="Ignore seen_leads.json (useful for live test)")
    args = ap.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not args.dry_run and (not token or not chat_id):
        print("[FATAL] Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env vars.")
        sys.exit(1)

    seen = {} if args.ignore_seen else load_seen()
    print(f"[INFO] Starting YouTube Shorts & CTR Thumbnails Sniper ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')})...")

    raw = []
    raw.extend(fetch_reddit_leads(max_age_hours=args.hours))
    raw.extend(fetch_freelancer_leads(max_age_hours=min(args.hours, 36.0)))
    raw.extend(fetch_remote_boards(max_age_hours=max(args.hours, 72.0)))

    fresh = []
    for lead in raw:
        if lead["id"] in seen:
            continue
        lead["score"] = score_lead(lead)
        if lead["score"] >= args.min_score:
            fresh.append(lead)

    # Sort by highest score then newest
    fresh.sort(key=lambda x: (x["score"], x["created_utc"]), reverse=True)
    print(f"[INFO] Scanned {len(raw)} strict Video/Thumbnail matches -> {len(fresh)} new qualified leads (>= {args.min_score}).")

    sent = 0
    for lead in fresh[: args.max_alerts]:
        pitch = build_smart_pitch(lead)
        if args.dry_run:
            print(f"\n--- [{lead['score']}/100] [{lead['category']}] {lead['source']} ---")
            print(f"TITLE:  {lead['title']}")
            print(f"BUDGET: {lead['budget']} | URL: {lead['url']}")
            print(f"HITS:   {lead['hits']}")
            print(f"PITCH:\n{pitch}")
            sent += 1
        else:
            if send_telegram_lead(token, chat_id, lead, pitch):
                seen[lead["id"]] = time.time()
                sent += 1
                time.sleep(0.8)

    if not args.dry_run and not args.ignore_seen and sent > 0:
        save_seen(seen)

    print(f"[DONE] Delivered {sent} high-intent YouTube Video & Thumbnail alerts.")


if __name__ == "__main__":
    main()
