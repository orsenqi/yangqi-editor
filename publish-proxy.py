# -*- coding: utf-8 -*-
"""
publish-proxy.py - 微信公众号草稿箱发布代理服务
公众号：扬旗而行
端口：8766

用法：python publish-proxy.py
"""

import json
import time
import os
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ============================================================
# 公众号配置（本地存储，不进浏览器）
# ============================================================
WX_APPID = "wx87ecc2f51089952a"
WX_APPSECRET = "0a99d5c632789572a715157c09ad3e60"

COVERS_DIR = os.path.join(os.path.dirname(__file__), "covers")
PORT = 8766

# ============================================================
# access_token 缓存（有效期2小时，自动刷新）
# ============================================================
_token_cache = {"token": None, "expires_at": 0}

def get_access_token():
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["token"]
    
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={WX_APPID}&secret={WX_APPSECRET}"
    resp = requests.get(url, timeout=10).json()
    
    if "access_token" not in resp:
        raise Exception(f"获取 access_token 失败: {resp}")
    
    _token_cache["token"] = resp["access_token"]
    _token_cache["expires_at"] = now + resp.get("expires_in", 7200)
    return _token_cache["token"]


def upload_cover_image(image_path: str) -> str:
    """上传封面图到微信永久素材，返回 thumb_media_id"""
    token = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?type=image&access_token={token}"
    with open(image_path, "rb") as f:
        resp = requests.post(url, files={"media": f}, timeout=30).json()
    if "media_id" not in resp:
        raise Exception(f"上传封面失败: {resp}")
    return resp["media_id"]


def create_draft(title: str, author: str, content: str, digest: str, thumb_media_id: str) -> str:
    """新建草稿，返回草稿 media_id"""
    token = get_access_token()
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    payload = {
        "articles": [{
            "title": title,
            "author": author,
            "digest": digest,
            "content": content,
            "content_source_url": "",
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }]
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    resp = requests.post(url, data=data, headers={"Content-Type": "application/json"}, timeout=30).json()
    if "media_id" not in resp:
        raise Exception(f"新建草稿失败: {resp}")
    return resp["media_id"]


# ============================================================
# HTTP 代理服务器
# ============================================================
class ProxyHandler(BaseHTTPRequestHandler):

    def _send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        try:
            if path == "/publish":
                # 必填：title, author, content, digest
                # 可选：cover_filename（covers/ 目录下的文件名）
                title = body.get("title", "")
                author = body.get("author", "扬旗而行")
                content = body.get("content", "")
                digest = body.get("digest", "")
                cover_filename = body.get("cover_filename", "")

                if not title or not content:
                    self._send_json(400, {"error": "title 和 content 不能为空"})
                    return

                # 上传封面
                thumb_media_id = ""
                if cover_filename:
                    cover_path = os.path.join(COVERS_DIR, cover_filename)
                    if os.path.exists(cover_path):
                        thumb_media_id = upload_cover_image(cover_path)

                # 如果没有封面，微信要求必须有 thumb_media_id，报错提示
                if not thumb_media_id:
                    self._send_json(400, {"error": "请先生成封面图（covers/ 目录下需有封面文件）"})
                    return

                draft_id = create_draft(title, author, content, digest, thumb_media_id)
                self._send_json(200, {"ok": True, "draft_id": draft_id, "message": "草稿已发布到公众号后台！"})

            elif path == "/token_test":
                # 测试接口：验证 AppID/AppSecret 是否有效
                token = get_access_token()
                self._send_json(200, {"ok": True, "token_prefix": token[:10] + "..."})

            else:
                self._send_json(404, {"error": "未知接口"})

        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/ping":
            self._send_json(200, {"ok": True, "service": "publish-proxy", "port": PORT})
        else:
            self._send_json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print(f"[publish-proxy] {fmt % args}")


if __name__ == "__main__":
    os.makedirs(COVERS_DIR, exist_ok=True)
    print(f"🚀 publish-proxy 启动，端口 {PORT}")
    print(f"   公众号：扬旗而行 ({WX_APPID})")
    print(f"   封面目录：{COVERS_DIR}")
    print(f"   测试：curl http://localhost:{PORT}/ping")
    HTTPServer(("127.0.0.1", PORT), ProxyHandler).serve_forever()
