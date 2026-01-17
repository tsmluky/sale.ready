import requests

def test_es_rss():
    # Try regions=es (Spain/Spanish) or lang=es
    # CryptoPanic usually uses 'regions' for filtering by language/region groups
    url = "https://cryptopanic.com/news/rss/"
    
    # Attempt 1: regions=es
    params = {"regions": "es", "filter": "hot"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    print("Testing regions=es...")
    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        if res.status_code == 200:
            print(f"Success! Length: {len(res.text)}")
            print(res.text[:500])
        else:
            print(f"Failed: {res.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # Attempt 2: lang=es
    print("\nTesting lang=es...")
    params2 = {"lang": "es", "filter": "hot"}
    try:
        res = requests.get(url, params=params2, headers=headers, timeout=10)
        if res.status_code == 200:
            print(f"Success! Length: {len(res.text)}")
            print(res.text[:500])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_es_rss()
