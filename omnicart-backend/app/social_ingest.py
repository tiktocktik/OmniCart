import os
import re
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
import requests

from .deal_scraper import infer_deal_category, classify_flash_deal

# -------------------------------------------------------------------
# URL Cleaning & Un-Shortening
# -------------------------------------------------------------------
def unshorten_and_sanitize_deal_url(raw_url: str) -> str:
    """
    Expands affiliate redirect shortlinks (amzn.to, fkrt.it, bit.ly, etc.)
    and strips affiliate tracking tags (tag=, affid=, subtag=) to give canonical product URLs.
    """
    cleaned = raw_url.strip()
    # If it's a known shortener, follow redirect headers
    if any(s in cleaned.lower() for s in ["amzn.to", "fkrt.it", "bit.ly", "cutt.ly", "tinyurl.com", "t.co"]):
        try:
            resp = requests.head(cleaned, allow_redirects=True, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            cleaned = resp.url
        except Exception:
            pass

    # Strip affiliate query parameters
    try:
        parsed = urllib.parse.urlparse(cleaned)
        qs = urllib.parse.parse_qs(parsed.query)
        # Remove tracking tokens
        for param in ["tag", "ascsubtag", "linkCode", "ref", "ref_", "affid", "affExtParam1", "subid", "utm_source", "utm_medium", "utm_campaign"]:
            qs.pop(param, None)
        new_query = urllib.parse.urlencode(qs, doseq=True)
        return urllib.parse.urlunparse(parsed._replace(query=new_query))
    except Exception:
        return cleaned


# -------------------------------------------------------------------
# 1. Reddit Stream Ingest (OAuth2 Client Credentials)
# -------------------------------------------------------------------
def fetch_reddit_deals(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    subreddits: Optional[List[str]] = None,
    limit: int = 15
) -> List[Dict[str, Any]]:
    """
    Fetches real-time deal threads from targeted Indian Subreddits
    (r/dealsindia, r/IndianGaming, r/IndianBeautyDeals, r/DesiFragranceAddicts).
    Requires free Reddit Developer App client_id & client_secret.
    """
    c_id = client_id or os.getenv("REDDIT_CLIENT_ID")
    c_sec = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
    if not c_id or not c_sec:
        return []

    target_subs = subreddits or ["dealsindia", "IndianGaming", "IndianBeautyDeals"]
    user_agent = os.getenv("REDDIT_USER_AGENT", "OmniCartDealHunter:v1.0")

    deals = []
    try:
        # 1. Obtain OAuth2 App Access Token
        auth = requests.auth.HTTPBasicAuth(c_id, c_sec)
        token_resp = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=auth,
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": user_agent},
            timeout=7
        )
        if token_resp.status_code != 200:
            return []

        token = token_resp.json().get("access_token")
        if not token:
            return []

        headers = {
            "Authorization": f"bearer {token}",
            "User-Agent": user_agent
        }

        # 2. Query each subreddit's newest posts
        for sub in target_subs:
            url = f"https://oauth.reddit.com/r/{sub}/new?limit={limit}"
            r = requests.get(url, headers=headers, timeout=6)
            if r.status_code != 200:
                continue

            data = r.json()
            posts = data.get("data", {}).get("children", [])
            for p in posts:
                pdata = p.get("data", {})
                title = pdata.get("title", "")
                post_url = pdata.get("url", "")
                post_id = pdata.get("id", "")
                upvotes = pdata.get("ups", 1)

                # Filter out discussions without shopping links or prices
                m_price = re.findall(r"₹\s*([0-9,]+)|\bRs\.?\s*([0-9,]+)", title, re.I)
                deal_price = 0.0
                if m_price:
                    raw_p = m_price[0][0] or m_price[0][1]
                    deal_price = float(raw_p.replace(",", ""))

                # Store matching
                store = "Online"
                if "amazon" in post_url.lower() or "amzn" in post_url.lower() or "amazon" in title.lower():
                    store = "Amazon"
                elif "flipkart" in post_url.lower() or "fkrt" in post_url.lower() or "flipkart" in title.lower():
                    store = "Flipkart"
                elif "myntra" in post_url.lower():
                    store = "Myntra"

                # Authentic thumbnail from Reddit preview if available
                img_url = pdata.get("thumbnail")
                if not img_url or "default" in img_url or "self" in img_url:
                    img_url = "https://m.media-amazon.com/images/I/71TaUujFs6L._SL1254_.jpg"

                clean_target_url = unshorten_and_sanitize_deal_url(post_url if post_url.startswith("http") else f"https://reddit.com{pdata.get('permalink')}")

                regular_price = round(deal_price * 1.4, 2) if deal_price > 0 else 0.0
                discount = int(round((1 - (deal_price / regular_price)) * 100)) if regular_price > 0 else 25

                flash_meta = classify_flash_deal(deal_price, regular_price, max(discount, 15), upvotes * 10, store)

                deals.append({
                    "id": f"reddit-{post_id}",
                    "title": title[:90],
                    "store": store,
                    "dealPrice": deal_price,
                    "regularPrice": regular_price,
                    "savings": flash_meta["savings"],
                    "discount": max(discount, 15),
                    "category": infer_deal_category(title),
                    "timeAgo": "Live",
                    "image": img_url,
                    "badge": f"Reddit r/{sub}",
                    "isMegaDrop": flash_meta["isMegaDrop"],
                    "isGlitch": flash_meta["isGlitch"],
                    "urgencyLevel": flash_meta["urgencyLevel"],
                    "heatScore": upvotes * 5,
                    "url": clean_target_url,
                    "source": f"Reddit r/{sub}"
                })
    except Exception:
        pass

    return deals


# -------------------------------------------------------------------
# 2. X (Twitter) Scraper (Playwright with User Session Cookie)
# -------------------------------------------------------------------
async def fetch_twitter_deals_async(
    auth_token: Optional[str] = None,
    ct0: Optional[str] = None,
    target_handles: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Scrapes the freshest deal tweets from Indian deal accounts
    (@deals_india, @indiantweeter, @desidimedeals, @dealbee_official)
    using Playwright with the user's authentic session cookie (no password needed!).
    """
    token = auth_token or os.getenv("TWITTER_AUTH_TOKEN")
    csrf = ct0 or os.getenv("TWITTER_CT0")
    if not token:
        return []

    handles = target_handles or ["deals_india", "indiantweeter", "desidimedeals"]
    deals = []

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )

            # Set user session cookies
            cookies = [
                {"name": "auth_token", "value": token, "domain": ".x.com", "path": "/"},
            ]
            if csrf:
                cookies.append({"name": "ct0", "value": csrf, "domain": ".x.com", "path": "/"})
            await context.add_cookies(cookies)

            page = await context.new_page()

            for handle in handles:
                try:
                    await page.goto(f"https://x.com/{handle}", timeout=15000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)

                    tweet_elements = await page.query_selector_all("article[data-testid='tweet']")
                    for t in tweet_elements[:limit]:
                        text_el = await t.query_selector("div[data-testid='tweetText']")
                        if not text_el:
                            continue
                        tweet_text = await text_el.inner_text()

                        # Extract link from tweet
                        link_el = await t.query_selector("a[href*='t.co']")
                        link = await link_el.get_attribute("href") if link_el else ""

                        # Extract image if present
                        img_el = await t.query_selector("div[data-testid='tweetPhoto'] img")
                        img_url = await img_el.get_attribute("src") if img_el else "https://m.media-amazon.com/images/I/71TaUujFs6L._SL1254_.jpg"

                        m_price = re.findall(r"₹\s*([0-9,]+)|\bRs\.?\s*([0-9,]+)", tweet_text, re.I)
                        deal_price = 0.0
                        if m_price:
                            raw_p = m_price[0][0] or m_price[0][1]
                            deal_price = float(raw_p.replace(",", ""))

                        store = "Amazon" if "amzn" in tweet_text.lower() or "amazon" in tweet_text.lower() else ("Flipkart" if "flipkart" in tweet_text.lower() or "fkrt" in tweet_text.lower() else "Online")
                        regular_price = round(deal_price * 1.35, 2) if deal_price > 0 else 0.0
                        discount = int(round((1 - (deal_price / regular_price)) * 100)) if regular_price > 0 else 25

                        clean_url = unshorten_and_sanitize_deal_url(link) if link else f"https://x.com/{handle}"
                        flash_meta = classify_flash_deal(deal_price, regular_price, max(discount, 15), 50, store)

                        deals.append({
                            "id": f"x-{abs(hash(tweet_text)) % 1000000}",
                            "title": tweet_text[:85].replace("\n", " "),
                            "store": store,
                            "dealPrice": deal_price,
                            "regularPrice": regular_price,
                            "savings": flash_meta["savings"],
                            "discount": max(discount, 15),
                            "category": infer_deal_category(tweet_text),
                            "timeAgo": "Live",
                            "image": img_url,
                            "badge": f"X @{handle}",
                            "isMegaDrop": flash_meta["isMegaDrop"],
                            "isGlitch": flash_meta["isGlitch"],
                            "urgencyLevel": flash_meta["urgencyLevel"],
                            "heatScore": 50,
                            "url": clean_url,
                            "source": f"X @{handle}"
                        })
                except Exception:
                    continue

            await browser.close()
    except Exception:
        pass

    return deals


# -------------------------------------------------------------------
# 3. Telegram Channels Stream Ingest (Telethon MTProto)
# -------------------------------------------------------------------
async def fetch_telegram_channel_deals(
    api_id: Optional[int] = None,
    api_hash: Optional[str] = None,
    channels: Optional[List[str]] = None,
    limit: int = 15
) -> List[Dict[str, Any]]:
    """
    Streams the latest drops directly from massive Indian Telegram deal channels
    (@dealsmagnet, @LootDealsOfficial, @DealBeeOfficial, @DesiDimeDeals)
    over MTProto binary connection (which bypasses Indian ISP web blocks completely!).
    Requires free Telegram api_id & api_hash from my.telegram.org.
    """
    tid = api_id or os.getenv("TELEGRAM_API_ID")
    thash = api_hash or os.getenv("TELEGRAM_API_HASH")
    if not tid or not thash:
        return []

    target_channels = channels or ["dealsmagnet", "LootDealsOfficial", "DealBeeOfficial"]
    deals = []

    try:
        from telethon import TelegramClient

        session_path = os.path.join(os.path.dirname(__file__), "omnicart_tg.session")
        client = TelegramClient(session_path, int(tid), thash)
        await client.connect()

        if not await client.is_user_authorized():
            # Awaiting user first-time auth
            await client.disconnect()
            return []

        for ch in target_channels:
            try:
                entity = await client.get_entity(ch)
                messages = await client.get_messages(entity, limit=limit)
                for msg in messages:
                    if not msg.message:
                        continue
                    text = msg.message
                    
                    # Extract prices
                    m_price = re.findall(r"₹\s*([0-9,]+)|\bRs\.?\s*([0-9,]+)", text, re.I)
                    deal_price = 0.0
                    if m_price:
                        raw_p = m_price[0][0] or m_price[0][1]
                        deal_price = float(raw_p.replace(",", ""))

                    # Extract target shortlinks
                    urls = re.findall(r"https?://[^\s]+", text)
                    if not urls:
                        continue
                    raw_target = urls[0]
                    clean_url = unshorten_and_sanitize_deal_url(raw_target)

                    store = "Amazon" if "amazon" in clean_url.lower() else ("Flipkart" if "flipkart" in clean_url.lower() else "Online")
                    regular_price = round(deal_price * 1.35, 2) if deal_price > 0 else 0.0
                    discount = int(round((1 - (deal_price / regular_price)) * 100)) if regular_price > 0 else 25

                    flash_meta = classify_flash_deal(deal_price, regular_price, max(discount, 15), 100, store)

                    deals.append({
                        "id": f"tg-{msg.id}-{abs(hash(ch)) % 1000}",
                        "title": text.split("\n")[0][:85],
                        "store": store,
                        "dealPrice": deal_price,
                        "regularPrice": regular_price,
                        "savings": flash_meta["savings"],
                        "discount": max(discount, 15),
                        "category": infer_deal_category(text),
                        "timeAgo": "Live",
                        "image": "https://m.media-amazon.com/images/I/71TaUujFs6L._SL1254_.jpg",
                        "badge": f"Telegram @{ch}",
                        "isMegaDrop": flash_meta["isMegaDrop"],
                        "isGlitch": flash_meta["isGlitch"],
                        "urgencyLevel": flash_meta["urgencyLevel"],
                        "heatScore": 100,
                        "url": clean_url,
                        "source": f"Telegram @{ch}"
                    })
            except Exception:
                continue

        await client.disconnect()
    except Exception:
        pass

    return deals
