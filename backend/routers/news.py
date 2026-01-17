import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any

router = APIRouter()

# RSS URL - Cointelegraph en Español
RSS_URL = "https://es.cointelegraph.com/rss"

# Smart Tagging Dictionary
KEYWORD_MAP = {
    "bitcoin": "BTC", "btc": "BTC",
    "ethereum": "ETH", "eth": "ETH",
    "solana": "SOL", "sol": "SOL",
    "xrp": "XRP", "ripple": "XRP",
    "cardano": "ADA", "ada": "ADA",
    "binance": "BNB", "bnb": "BNB",
    "dogecoin": "DOGE", "doge": "DOGE",
    "shiba": "SHIB", "pepe": "PEPE",
    "avalanche": "AVAX", "avax": "AVAX",
    "polygon": "MATIC", "matic": "MATIC",
    "chainlink": "LINK", "link": "LINK",
    "polkadot": "DOT", "dot": "DOT",
    "litecoin": "LTC", "ltc": "LTC",
    "stellar": "XLM", "xlm": "XLM",
    "market": "MKT", "mercado": "MKT",
    "sec": "REG", "etf": "ETF", "defi": "DEFI", "nft": "NFT",
    "crypto": "CRYPTO", "cripto": "CRYPTO",
    "blockchain": "TECH", "ai": "AI"
}

def extract_tags_from_text(text: str) -> List[Dict[str, str]]:
    """Generates tags based on Keywords found in title."""
    found_tags = []
    text_lower = text.lower()
    added_codes = set()
    
    for keyword, code in KEYWORD_MAP.items():
        if f" {keyword} " in f" {text_lower} " or \
           f" {keyword}," in f" {text_lower} " or \
           f" {keyword}." in f" {text_lower} ":
            
            if code not in added_codes:
                found_tags.append({"code": code, "title": keyword.title(), "slug": code.lower()})
                added_codes.add(code)
    
    return found_tags[:3]

def parse_rss_to_news_items(xml_content: str) -> List[Dict[str, Any]]:
    items = []
    try:
        root = ET.fromstring(xml_content)
        channel = root.find("channel")
        if channel is None: return []
            
        for i, item in enumerate(channel.findall("item")):
            title = item.find("title").text if item.find("title") is not None else "No Title"
            
            # Cointelegraph uses standard <link> correctly
            link = ""
            link_tag = item.find("link")
            if link_tag is not None:
                link = link_tag.text
            
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            
            # Smart Tags
            currencies = extract_tags_from_text(title)
            
            # Also check RSS categories if needed, but Smart Tags are more consistent for tickers
            if not currencies:
                # Try to use RSS category as fallback tag
                cat = item.find("category")
                if cat is not None and cat.text:
                     currencies = [{"code": cat.text[:4].upper(), "title": cat.text, "slug": "info"}]
                else:
                     currencies = [{"code": "INFO", "title": "Info", "slug": "info"}]

            news_id = int(datetime.now().timestamp()) + i
            
            items.append({
                "id": news_id,
                "title": title,
                "url": link,
                "domain": "es.cointelegraph.com",
                "published_at": pub_date, 
                "currencies": currencies, 
                "source": {
                    "title": "Cointelegraph",
                    "region": "es",
                    "domain": "cointelegraph.com"
                },
                "kind": "news"
            })
            
            if len(items) >= 20: break
                
    except Exception as e:
        print(f"[RSS Parser] Error: {e}")
        
    return items

@router.get("/")
async def get_news(
    limit: Optional[int] = Query(20, description="Items limit")
):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(RSS_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            news_items = parse_rss_to_news_items(response.text)
            return {"results": news_items}
        else:
            print(f"[News] RSS Error: {response.status_code}")
            return {"results": []}
            
    except Exception as e:
        print(f"[News] Exception: {e}")
        return {"results": []}
