import re
import requests
import random
import uvicorn
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="TeraBox Ultimate Downloader API")

# وہی ورکرز جو آپ کی فائل میں تھے
WORKERS_ENDPOINTS = [
    "https://terabox.hnn.workers.dev",
    "https://plain-grass-58b2.comprehensiveaquamarine.workers.dev",
    "https://bold-hall-f23e.7rochelle.workers.dev",
    "https://winter-thunder-0360.belitawhite.workers.dev"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
}

def extract_surl(url: str):
    """لنک سے شارٹ یو آر ایل نکالنے والا فنکشن"""
    if 'surl=' in url:
        return url.split('surl=')[-1].split('&')[0]
    
    # اگر ڈائریکٹ لنک ہو تو ریگولر ایکسپریشن سے نکالیں
    match = re.search(r'\/s\/1([^ &?\/]+)', url)
    if match:
        return "1" + match.group(1)
    return None

@app.get("/api/download")
async def get_download_link(url: str = Query(..., description="TeraBox Link")):
    surl = extract_surl(url)
    if not surl:
        raise HTTPException(status_code=400, detail="Invalid TeraBox URL format")

    # پروکسی ورکرز کے ذریعے کوشش کریں
    # 
    for endpoint in WORKERS_ENDPOINTS:
        try:
            payload = {
                "shorturl": surl,
                "pwd": "" # اگر پاسورڈ ہو تو یہاں ایڈ ہو سکتا ہے
            }
            
            # ورکر کو ریکویسٹ بھیجنا (یہ وہی میتھڈ ہے جو workers.py میں تھا)
            response = requests.post(f"{endpoint}/api/get-info", json=payload, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    # اگر ورکر سے ڈیٹا مل گیا تو واپس کر دیں
                    return {
                        "status": "success",
                        "server_used": endpoint,
                        "file_name": data.get("list", [{}])[0].get("server_filename"),
                        "size": data.get("list", [{}])[0].get("size"),
                        "download_link": data.get("downloadLink"),
                        "direct_link": data.get("direct_link")
                    }
        except Exception as e:
            print(f"Worker {endpoint} failed: {e}")
            continue # اگر ایک ورکر فیل ہو تو اگلے پر جائیں

    raise HTTPException(status_code=500, detail="All proxy workers failed to process this link.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
