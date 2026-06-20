import requests

url = "http://quincy.torontocast.com:2020/stream.mp3"

headers = {
    "Icy-MetaData": "1",
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(
    url,
    headers=headers,
    stream=True,
    timeout=15
)

metaint = int(r.headers["icy-metaint"])

stream = r.raw

stream.read(metaint)

length = ord(stream.read(1))

metadata = stream.read(length * 16)

print(metadata.decode(
    "utf-8",
    errors="ignore"
))