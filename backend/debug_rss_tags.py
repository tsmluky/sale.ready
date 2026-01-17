import requests
import xml.etree.ElementTree as ET

def check_tags():
    url = "https://cryptopanic.com/news/rss/?regions=es"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(res.text)
        items = root.find("channel").findall("item")
        
        print(f"Checking {len(items)} items for tags/markup...")
        
        for i, item in enumerate(items[:3]):
            print(f"\n[Item {i}]")
            # Print all tag names in the item
            tags = [elem.tag for elem in item]
            print(f"Tags found: {tags}")
            
            # Check for specific category-like tags
            categories = item.findall("category")
            if categories:
                print(f"Categories: {[c.text for c in categories]}")
                
            # Check title for keywords
            title = item.find("title").text
            print(f"Title: {title}")

    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    check_tags()
