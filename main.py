from fastapi import FastAPI, HTTPException
import re
import requests
import random
import uvicorn

app = FastAPI(title="TeraBox Downloader API")

# وہی ہیڈرز جو آپ کی اوریجنل فائل میں تھے
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

class TeraBoxExtractor:
    def __init__(self):
        self.session = requests.Session()

    def get_download_data(self, url: str):
        try:
            # 1. شارٹ یو آر ایل نکالنا
            response = self.session.get(url, allow_redirects=True)
            surl_match = re.search(r'surl=([^ &]+)', str(response.url))
            if not surl_match:
                return {"error": "Invalid TeraBox URL"}
            
            short_url = surl_match.group(1)
            
            # 2. ٹوکنز نکالنا (jsToken اور Browser ID)
            # آپ کی terabox1.py والی لاجک یہاں استعمال ہو رہی ہے
            api_url = f"https://www.terabox.app/wap/share/filelist?surl={short_url}"
            res = self.session.get(api_url, headers=HEADERS)
            
            js_token = re.search(r'jsToken\s*=\s*["\']([^"\']+)["\']', res.text).group(1)
            browser_id = "".join(random.choices("0123456789abcdefghijklmnopqrstuvwxyz", k=32))
            
            # 3. فائل کی معلومات حاصل کرنا
            info_url = f"https://www.terabox.com/api/shorturlinfo?app_id=250528&shorturl=1{short_url}&root=1"
            self.session.cookies.update({'browserid': browser_id})
            
            info_res = self.session.get(info_url, headers=HEADERS).json()
            
            if info_res.get('errno') != 0:
                return {"error": "Could not fetch file info"}

            # ڈیٹا کو ترتیب دینا
            file_info = info_res['list'][0]
            download_payload = {
                "jsToken": js_token,
                "timestamp": info_res['timestamp'],
                "sign": info_res['sign'],
                "uk": info_res['uk'],
                "shareid": info_res['shareid'],
                "fs_id": file_info['fs_id'],
                "filename": file_info['server_filename'],
                "size": file_info['size']
            }
            
            return download_payload

        except Exception as e:
            return {"error": str(e)}

extractor = TeraBoxExtractor()

@app.get("/api/download")
async def get_link(url: str):
    data = extractor.get_download_data(url)
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])
    return data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
