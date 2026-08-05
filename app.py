def get_video_info(url):
    """دریافت اطلاعات ویدیو (عنوان، کیفیت‌ها) با پشتیبانی از کوکی"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'extract_flat': False,  # اطلاعات کامل رو بگیر
        'ignoreerrors': True,   # خطاهای جزئی رو نادیده بگیر
        'force_generic_extractor': False,  # از اکسترکتور اختصاصی استفاده کن
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # اگر اطلاعات ویدیو موجود نباشه
            if not info:
                return {'error': 'اطلاعات ویدیو پیدا نشد'}
            
            # استخراج فرمت‌های معتبر
            formats = []
            for f in info.get('formats', []):
                # فرمت باید ویدیو و صدا داشته باشه
                has_video = f.get('vcodec') != 'none'
                has_audio = f.get('acodec') != 'none'
                format_id = f.get('format_id')
                
                if has_video and has_audio and format_id:
                    # فیلتر کردن فرمت‌های DASH و غیرمعمول
                    format_note = f.get('format_note', '').lower()
                    if 'dash' not in format_note and 'live' not in format_note:
                        # تبدیل size به MB
                        filesize = f.get('filesize')
                        if filesize:
                            filesize_mb = round(filesize / (1024 * 1024), 2)
                        else:
                            filesize_mb = 'N/A'
                        
                        formats.append({
                            'quality': f.get('format_note', 'Unknown'),
                            'ext': f.get('ext', 'mp4'),
                            'format_id': format_id,
                            'filesize': filesize_mb,
                            'height': f.get('height', 'N/A'),
                            'width': f.get('width', 'N/A')
                        })
            
            # مرتب‌سازی بر اساس کیفیت (از بالا به پایین)
            formats.sort(key=lambda x: x.get('height', 0) if isinstance(x.get('height'), (int, float)) else 0, reverse=True)
            
            # محدود کردن به ۵ فرمت با کیفیت بالا
            formats = formats[:5]
            
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'formats': formats
            }
            
    except Exception as e:
        # خطاهای رایج رو مدیریت کن
        error_msg = str(e)
        if 'Sign in to confirm' in error_msg:
            return {'error': 'لطفاً کوکی را به‌روزرسانی کنید. از دستور python get_cookies.py استفاده کنید.'}
        elif 'format' in error_msg.lower() and 'not available' in error_msg.lower():
            return {'error': 'فرمت درخواستی برای این ویدیو در دسترس نیست. کیفیت دیگری را انتخاب کنید.'}
        else:
            return {'error': f'خطا: {error_msg[:200]}'}  # محدود کردن طول پیام خطا
