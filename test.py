import subprocess

cmd = [
    'yt-dlp',
    '-f', 'best[ext=mp4]/best',
    '-o', 'downloads/test.mp4',
    'https://youtu.be/_7dxX6mF0Iw?si=kfCA3r1oLTyogloY'
]

result = subprocess.run(cmd, capture_output=True, text=True)
print("خروجی:", result.stdout)
print("خطا:", result.stderr)
print("کد:", result.returncode)
