import requests

def get_current_song(url):
    try:
        r = requests.get(
            url,
            headers={"Icy-MetaData":"1","User-Agent":"Mozilla/5.0"},
            stream=True,
            timeout=10
        )
        if "icy-metaint" not in r.headers:
            return "Unknown Track"
            
        metaint = int(r.headers["icy-metaint"])
        s = r.raw
        s.read(metaint)
        length = ord(s.read(1))
        metadata = s.read(length * 16).decode("utf-8", errors="ignore")

        if "StreamTitle='" in metadata:
            start = metadata.find("StreamTitle='") + 13
            end = metadata.find("';", start)
            return metadata[start:end]

        return "Unknown Track"
    except Exception as e:
        print("Metadata Error:", e)
        return "Unknown Track"
