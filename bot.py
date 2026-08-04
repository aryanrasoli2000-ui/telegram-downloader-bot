def download_video(url, quality="best"):
    os.makedirs("downloads", exist_ok=True)
    
    # اضافه کردن --cookies به دستورات
    base_cmd = ['yt-dlp', '--cookies', 'cookies.txt', '--no-warnings', '--quiet']
    
    if quality == "audio":
        cmd = base_cmd + [
            '-f', 'bestaudio/best',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '192',
            '-o', 'downloads/%(id)s.%(ext)s',
            url
        ]
    else:
        cmd = base_cmd + [
            '-f', f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]',
            '-o', 'downloads/%(id)s.%(ext)s',
            url
        ]
    
    try:
        subprocess.run(cmd, check=True, timeout=300)
        files = os.listdir('downloads')
        if files:
            return os.path.join('downloads', files[-1])
    except:
        pass
    return None
