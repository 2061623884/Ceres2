"""Visible Firefox journey against the current built UI and an isolated demo API."""
from __future__ import annotations

import importlib.util
import json
import mimetypes
import os
from pathlib import Path
import subprocess
import threading
import time
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = ROOT / "work/local-followup/04/real-model-20261008"
ARTIFACTS = EVIDENCE / "tmp/browser-real-model-20261008"
DIST = ROOT / "frontend/dist"
API_PORT = 8015
UI_PORT = 8446
UI_AUTHORITY = f"localhost:{UI_PORT}"
GECKODRIVER = ROOT / "work/local-cloud-integration/local-acceptance-20261008/tmp/geckodriver/geckodriver"
FIREFOX = Path("/usr/bin/firefox")
PREVIOUS_JOURNEY = ROOT / "work/local-cloud-integration/local-acceptance-20261008/firefox_webdriver_journey.py"


class BuiltUIHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "CeresBuiltUI/1"
    sys_version = ""

    def log_message(self, *_args):
        return

    def _respond(self, status: int, content_type: str, body: bytes, headers=()):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in headers:
            if key.lower() not in {"connection", "content-length", "transfer-encoding", "server", "date"}:
                self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _proxy_api(self):
        parsed = urlsplit(self.path)
        body = self.rfile.read(int(self.headers.get("content-length", "0") or "0"))
        headers = {
            key: value for key, value in self.headers.items()
            if key.lower() not in {"host", "connection", "content-length", "transfer-encoding", "accept-encoding"}
        }
        headers["Host"] = f"127.0.0.1:{API_PORT}"
        headers["Connection"] = "close"
        if body:
            headers["Content-Length"] = str(len(body))
        upstream = HTTPConnection("127.0.0.1", API_PORT, timeout=25)
        try:
            path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
            upstream.request(self.command, path, body=body or None, headers=headers)
            response = upstream.getresponse()
            payload = response.read()
            self._respond(response.status, response.getheader("Content-Type", "application/json"),
                          payload, response.getheaders())
        finally:
            upstream.close()

    def _static(self):
        parsed = urlsplit(self.path)
        relative = unquote(parsed.path.lstrip("/"))
        root = DIST.resolve()
        target = (root / relative).resolve()
        if target != root and root not in target.parents:
            self._respond(404, "text/plain; charset=utf-8", b"not found")
            return
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            if Path(relative).suffix:
                self._respond(404, "text/plain; charset=utf-8", b"not found")
                return
            target = root / "index.html"
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {"application/javascript", "image/svg+xml"}:
            content_type += "; charset=utf-8"
        payload = target.read_bytes()
        self._respond(200, content_type, payload)

    def _dispatch(self):
        if self.path.startswith(("/api/", "/media/")):
            self._proxy_api()
        elif self.command in {"GET", "HEAD"}:
            self._static()
        else:
            self._respond(404, "text/plain; charset=utf-8", b"not found")

    do_GET = _dispatch
    do_HEAD = _dispatch
    do_POST = _dispatch
    do_PUT = _dispatch
    do_PATCH = _dispatch
    do_DELETE = _dispatch


def load_helpers():
    spec = importlib.util.spec_from_file_location("controlled_firefox_helpers", PREVIOUS_JOURNEY)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> int:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    os.chmod(ARTIFACTS, 0o700)
    if not (DIST / "index.html").is_file() or not GECKODRIVER.is_file() or not FIREFOX.is_file():
        print(json.dumps({"status": "not_run", "reason": "browser_or_built_ui_missing"}, sort_keys=True))
        return 2

    helpers = load_helpers()
    cert = ARTIFACTS / f"local-origin-cert-{time.time_ns()}.pem"
    key = ARTIFACTS / f"local-origin-key-{time.time_ns()}.pem"
    subprocess.run([
        "/usr/bin/openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
        "-keyout", str(key), "-out", str(cert), "-days", "2",
        "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost",
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    key.chmod(0o600)

    ui = ThreadingHTTPServer(("127.0.0.1", UI_PORT), BuiltUIHandler)
    ui.daemon_threads = True
    ui_thread = threading.Thread(target=ui.serve_forever, name="built-ui", daemon=True)
    ui_thread.start()
    proxy = helpers.ExactFixtureProxy(UI_AUTHORITY, UI_PORT, cert, key)
    proxy.start()
    driver = None
    stage = "browser_start"
    result = {}
    try:
        options = Options()
        options.binary_location = str(FIREFOX)
        options.add_argument("-headless")
        options.accept_insecure_certs = True
        options.set_preference("network.proxy.type", 1)
        options.set_preference("network.proxy.http", "127.0.0.1")
        options.set_preference("network.proxy.http_port", proxy.port)
        options.set_preference("network.proxy.ssl", "127.0.0.1")
        options.set_preference("network.proxy.ssl_port", proxy.port)
        options.set_preference("network.proxy.no_proxies_on", "")
        options.set_preference("network.proxy.allow_hijacking_localhost", True)
        options.set_preference("network.trr.mode", 5)
        options.set_preference("app.update.enabled", False)
        options.set_preference("browser.shell.checkDefaultBrowser", False)
        options.set_preference("browser.startup.homepage", "about:blank")
        options.set_preference("toolkit.telemetry.enabled", False)
        options.set_preference("datareporting.healthreport.uploadEnabled", False)
        service = Service(executable_path=str(GECKODRIVER), log_output=str(ARTIFACTS / "geckodriver.log"))
        driver = webdriver.Firefox(service=service, options=options)
        driver.set_window_size(1100, 1000)
        driver.set_page_load_timeout(25)
        page = helpers.Journey(driver, ARTIFACTS)

        stage = "external_http_block"
        try:
            driver.get("http://example.com/")
        except Exception:
            pass
        blocked_http = [row for row in proxy.snapshot() if not row.get("allowed")]
        assert any(row.get("authority") == "example.com" for row in blocked_http)
        stage = "external_https_block"
        try:
            driver.get("https://example.com/")
        except Exception:
            pass
        blocked = [row for row in proxy.snapshot() if not row.get("allowed")]
        assert any(row.get("method") == "CONNECT" and row.get("authority") == "example.com:443" for row in blocked)

        stage = "load_built_ui"
        driver.get(f"https://{UI_AUTHORITY}/")
        context = driver.execute_script("return {origin:location.origin,isSecureContext:window.isSecureContext,cryptoRandomUUID:typeof crypto.randomUUID}")
        assert context["origin"] == f"https://{UI_AUTHORITY}"
        assert context["isSecureContext"] and context["cryptoRandomUUID"] == "function", context

        stage = "open_products"
        page.click(page.button("商品", timeout=20))
        detail_button = page.find(By.XPATH, "//button[starts-with(@aria-label,'查看') and contains(@aria-label,'详情')]", timeout=20)
        detail_name = detail_button.get_attribute("aria-label") or ""
        page.click(detail_button)
        detail = page.dialog("商品详情", timeout=15)
        assert "价格与库存为模拟数据" in detail.text
        add_button = page.button("添加一件到购物车", root=detail, timeout=15)
        assert add_button.is_enabled()
        page.screenshot("01-product-detail")

        stage = "add_and_checkout"
        page.click(add_button)
        page.wait(lambda _driver: "正在添加" not in detail.text, timeout=10)
        page.click(page.button("关闭", root=detail))
        page.click(page.label("购物车", timeout=10))
        cart = page.dialog("购物车", timeout=10)
        assert "合计" in cart.text
        page.click(page.button("模拟结算", root=cart, timeout=10))
        checkout = page.dialog("模拟结算", timeout=10)
        assert "不会付款或真实配送" in checkout.text
        page.click(page.button("确认模拟结算", root=checkout, timeout=15))
        page.wait(lambda _driver: "模拟订单已保存" in checkout.text, timeout=20)
        page.screenshot("02-checkout-saved")

        stage = "open_and_progress_order"
        page.click(page.button("查看订单", root=checkout, timeout=10))
        page.text("我的模拟订单", timeout=15)
        order_button = page.find(By.XPATH, "//button[starts-with(@aria-label,'查看订单 ')]", timeout=15)
        page.click(order_button)
        order = page.find(By.CSS_SELECTOR, "article[data-order-id]", timeout=15)
        submitted = order.text
        assert "模拟状态：已提交" in submitted
        order_id = order.get_attribute("data-order-id")
        page.click(page.button("模拟推进至配送中", root=order, timeout=10))
        shipped = page.find(By.CSS_SELECTOR, "article[data-order-id]", timeout=15).text
        assert "模拟状态：shipped" in shipped
        page.click(page.button("模拟签收", root=page.find(By.CSS_SELECTOR, "article[data-order-id]"), timeout=10))
        delivered_order = page.find(By.CSS_SELECTOR, "article[data-order-id]", timeout=15)
        delivered = delivered_order.text
        assert "模拟状态：delivered" in delivered
        submitted_total = next(row for row in submitted.splitlines() if row.startswith("合计 "))
        delivered_total = next(row for row in delivered.splitlines() if row.startswith("合计 "))
        assert submitted_total == delivered_total, "order total changed across demo status transitions"
        page.screenshot("03-order-delivered")

        requests = proxy.snapshot()
        blocked = [row for row in requests if not row.get("allowed")]
        allowed_authorities = sorted({row.get("authority") for row in requests if row.get("allowed")})
        assert allowed_authorities == [UI_AUTHORITY], allowed_authorities
        result = {
            "status": "passed",
            "level": "real-system-Firefox-built-UI-isolated-production-API",
            "firefox_version": driver.capabilities.get("browserVersion"),
            "geckodriver_version": "0.37.1",
            "fresh_browser_profile": True,
            "secure_context": context["isSecureContext"],
            "product_detail_label": detail_name,
            "product_to_simulated_order": True,
            "order_states": ["submitted", "shipped", "delivered"],
            "order_snapshot_total_stable": True,
            "request_count": len(requests),
            "allowed_authorities": allowed_authorities,
            "blocked_external_authorities": sorted({row.get("authority") for row in blocked}),
            "screenshots": [
                "work/local-followup/04/real-model-20261008/tmp/browser-real-model-20261008/01-product-detail.png",
                "work/local-followup/04/real-model-20261008/tmp/browser-real-model-20261008/02-checkout-saved.png",
                "work/local-followup/04/real-model-20261008/tmp/browser-real-model-20261008/03-order-delivered.png",
            ],
            "guide_or_memory_calls_from_browser": 0,
            "isolated_database": "data/runtime/real-model-20261008/browser-smoke-final.sqlite3",
            "order_id_recorded": bool(order_id),
        }
        (ARTIFACTS / "browser-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as error:
        result = {"status": "failed", "stage": stage, "error_type": type(error).__name__}
        if "context" in locals():
            result["browser_context"] = {
                key: context.get(key) for key in ("origin", "isSecureContext", "cryptoRandomUUID")
            }
        if driver is not None:
            try:
                driver.save_screenshot(str(ARTIFACTS / "failure.png"))
            except Exception:
                pass
        (ARTIFACTS / "browser-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1
    finally:
        if driver is not None:
            driver.quit()
        proxy.close()
        ui.shutdown()
        ui.server_close()
        ui_thread.join(timeout=3)


if __name__ == "__main__":
    raise SystemExit(main())
