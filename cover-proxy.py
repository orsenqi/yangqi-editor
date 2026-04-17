"""
封面生成代理服务
智谱 CogView-4 图片生成 API 本地代理
解决浏览器跨域问题

启动方式：python cover-proxy.py
代理地址：http://localhost:8765/generate

依赖：pip install requests
"""

import json
import logging
import os
import sys

# 如果没有 requests 就用内置urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.parse
    import urllib.error
    HAS_REQUESTS = False

from http.server import HTTPServer, BaseHTTPRequestHandler

# ==================== 配置区 ====================
# 智谱 API Key（从环境变量读取，或直接填在这里）
ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', 'b34e1f48e6464386bb21a8bf00e9a306.JQ43UuiU44EIfhB4')
ZHIPU_API_URL = 'https://open.bigmodel.cn/api/paas/v4/images/generations'
# ==================== 配置区 ====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger()


def generate_with_zhipu(prompt: str, model: str = 'cogview-4-250304') -> dict:
    """调用智谱 CogView-4 API 生成图片"""
    headers = {
        'Authorization': f'Bearer {ZHIPU_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': model,
        'prompt': prompt,
        'size': '1024x1024',
        'quality': 'hd',
    }

    log.info(f'请求智谱 API，模型={model}，提示词长度={len(prompt)}')
    log.info(f'提示词预览：{prompt[:80]}...')

    if HAS_REQUESTS:
        resp = requests.post(ZHIPU_API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()
    else:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            ZHIPU_API_URL,
            data=data,
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode('utf-8'))


class ProxyHandler(BaseHTTPRequestHandler):
    """处理 /generate 请求的 HTTP Handler"""

    def log_message(self, format, *args):
        """用自定义日志格式"""
        log.info(format % args)

    def do_POST(self):
        if self.path != '/generate':
            self.send_error(404, 'Not Found')
            return

        # 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        try:
            body = self.rfile.read(content_length)
            req_data = json.loads(body.decode('utf-8'))
            prompt = req_data.get('prompt', '')
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._send_error(400, f'请求体解析错误: {e}')
            return

        if not prompt:
            self._send_error(400, 'prompt 不能为空')
            return

        # 调用智谱 API
        try:
            result = generate_with_zhipu(prompt)
            image_url = result.get('data', [{}])[0].get('url', '')
            if not image_url:
                self._send_error(500, '智谱返回数据缺少 url 字段')
                return
            log.info(f'生成成功：{image_url[:80]}...')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'url': image_url}, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            log.error(f'智谱 API 调用失败：{e}')
            self._send_error(502, f'智谱 API 调用失败: {e}')

    def do_OPTIONS(self):
        """支持 CORS 预检"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run(port: int = 8765):
    server = HTTPServer(('127.0.0.1', port), ProxyHandler)
    log.info(f'智谱封面生成代理启动成功！')
    log.info(f'监听地址：http://127.0.0.1:{port}/generate')
    log.info(f'按 Ctrl+C 停止服务')
    log.info(f'计费：智谱 CogView-4，每次 0.06 元')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info('服务已停止')
        server.shutdown()


if __name__ == '__main__':
    run()
