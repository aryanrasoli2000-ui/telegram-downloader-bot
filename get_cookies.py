import browser_cookie3

cookies = browser_cookie3.chrome(domain_name='.youtube.com')

with open('cookies.txt', 'w') as f:
    f.write("# Netscape HTTP Cookie File\n")
    for cookie in cookies:
        if 'youtube' in cookie.domain:
            f.write(f"{cookie.domain}\tTRUE\t{cookie.path}\t{'TRUE' if cookie.secure else 'FALSE'}\t{int(cookie.expires) if cookie.expires else 0}\t{cookie.name}\t{cookie.value}\n")

print("✅ کوکی‌ها با موفقیت استخراج شدند!")
