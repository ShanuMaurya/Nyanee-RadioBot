import urllib.request
import re

url = "https://web.archive.org/web/20211225233008/https://nyanee.vip/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    print(f"Fetching {url}...")
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
    
    # Find all JS and CSS chunks
    chunks = re.findall(r'href="(/web/[^"]+\.css)"|src="(/web/[^"]+\.js)"', html)
    chunks = [c[0] or c[1] for c in chunks if c[0] or c[1]]
    
    print(f"Found {len(chunks)} JS/CSS chunks to analyze for hidden assets...")
    
    found_assets = set()
    
    for chunk in chunks:
        chunk_url = "https://web.archive.org" + chunk
        try:
            with urllib.request.urlopen(urllib.request.Request(chunk_url, headers={'User-Agent': 'Mozilla/5.0'})) as res:
                content = res.read().decode('utf-8', errors='ignore')
                # Look for common asset extensions
                assets = re.findall(r'([a-zA-Z0-9_./-]+\.(?:png|jpg|jpeg|svg|gif|webp))', content)
                for a in assets:
                    if len(a) > 4 and not a.startswith('http'):
                        found_assets.add(a)
        except Exception as e:
            pass

    print("\n--- EXTRACTED ASSETS ---")
    for asset in sorted(list(found_assets)):
        print("https://web.archive.org/web/20211225233008/https://nyanee.vip" + (asset if asset.startswith('/') else '/' + asset))

except Exception as e:
    print("Error:", e)
