import os
import urllib.request

asset_urls = [
    "https://cdn.discordapp.com/attachments/417069289313402883/874301894711996496/unknown.png",
    "https://cdn.discordapp.com/attachments/417069289313402883/917876444129005578/Soundz.gif",
    "https://cdn.discordapp.com/avatars/388042065889722380/7080a3d25c33792e7b5cd528f10db550.webp",
    "https://cdn.discordapp.com/avatars/397879594109108226/9074b33142746bd3832a04265ca537b6.webp",
    "https://cdn.plyr.io/3.6.8/plyr.svg",
    "https://i1.wp.com/myotakuworld.com/wp-content/uploads/2020/04/happy-anime.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/badges.bf3f534a.svg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/banner.8e3da7b5.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/icons.3cff5575.svg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/icons2.7a8fa79e.svg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/default.png",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/default.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/nagataro.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/1.f8d2045c.png",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/action.dfdbe7e1.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/adventure.07d94537.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/cars.8a9478f1.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/comedy.c2c30466.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/dementia.d992e936.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/demons.01a94e87.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/drama.0eb128d6.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/ecchi.12b86d8a.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/fantasy.66af2b93.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/game.49921b52.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/harem.3a773bf9.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/hentai.36db02d9.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/historical.0c4556f6.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/horror.57c0fd6d.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/images.816958c2.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/josei.f654a618.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/kids.a1f30d17.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/logo_dark_christmas.1b494550.png",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/logo_light.5d2541bf.png",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/magic.e707b415.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/martial_arts.e52d4308.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/mecha.a1a5e310.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/military.9f5d7cd1.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/music.375b6f6f.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/mystery.84a671fb.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/parody.5f6f09ba.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/police.e3c14ed5.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/psychological.683c3667.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/recovery1.45a8a23d.png",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/recovery2.280ad7a1.png",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/recovery3.6e4131cb.png",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/romance.914e4154.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/samurai.f2717810.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/school.881c5b6d.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/sci-fi.943fb1b6.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/seasons.a529bd20.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/seinen.bdf4e1af.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/shoujo.e6cbf1c1.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/shoujo_ai.a01738ec.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/shounen.6fc730f3.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/shounen_ai.0e6bc566.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/slice_of_life.d8478e17.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/space.b60577ab.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/sports.2664d1d4.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/super_power.9bbd04ae.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/supernatural.a496295b.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/thriller.c383dddc.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/thumb.f7ccd42f.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/trending.dfdbe7e1.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/vampire.d5ee4aed.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/yaoi.5a87c580.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/static/media/yuri.edee2c1f.jpg",
    "https://web.archive.org/web/20211225233008/https://nyanee.vip/window.svg"
]

download_dir = r"d:\zip\radio_bot_v2\web\public\old_assets"
os.makedirs(download_dir, exist_ok=True)

print(f"Downloading {len(asset_urls)} assets into {download_dir}...")

for url in asset_urls:
    # Get the file name from the URL
    filename = url.split('/')[-1]
    
    # Strip the webpack hash if it exists (e.g. action.dfdbe7e1.jpg -> action.jpg)
    parts = filename.split('.')
    if len(parts) >= 3 and len(parts[-2]) == 8: # checks for 8-char hash
        clean_filename = parts[0] + '.' + parts[-1]
    else:
        clean_filename = filename
        
    save_path = os.path.join(download_dir, clean_filename)
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = response.read()
            with open(save_path, 'wb') as f:
                f.write(data)
        print(f"Downloaded: {clean_filename}")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")

print("\nFinished downloading all assets!")
