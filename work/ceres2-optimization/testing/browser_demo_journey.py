"""Exercise the demo shopping-to-quality-case journey in native Firefox."""

from __future__ import annotations

import base64
import http.client
import http.server
import json
import os
import subprocess
import threading
import time
import traceback
import urllib.error
import urllib.request
import zlib
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[3]
TESTING = Path(__file__).resolve().parent
TMP = TESTING / "tmp" / "browser-demo"
DIST = ROOT / "frontend" / "dist"
GECKODRIVER = TMP.parent / "browser" / "geckodriver-0.37.1" / "geckodriver"
GECKO_PORT = 4444
FRONTEND_PORT = 18444
BACKEND_PORT = 18013
BASE_URL = f"http://127.0.0.1:{FRONTEND_PORT}"
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
OPERATOR_TOKEN = "browser-test-only-token"
ELEMENT_KEY = "element-6066-11e4-a52e-4f735466cecf"


class BrowserFailure(RuntimeError):
    pass


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    server_version = "CeresTesterProxy/1.0"

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, directory=str(DIST), **kwargs)

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def copyfile(self, source: Any, outputfile: Any) -> None:
        try:
            super().copyfile(source, outputfile)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _proxy(self) -> None:
        parsed = urlsplit(self.path)
        body = self.rfile.read(int(self.headers.get("Content-Length", "0"))) if self.command in {"POST", "PUT", "PATCH"} else None
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "connection", "content-length", "accept-encoding"}
        }
        connection = http.client.HTTPConnection("127.0.0.1", BACKEND_PORT, timeout=90)
        try:
            connection.request(self.command, self.path, body=body, headers=headers)
            response = connection.getresponse()
            data = response.read()
            status = response.status
            response_headers = response.getheaders()
        finally:
            connection.close()
        self.server.api_calls.append({"method": self.command, "path": parsed.path, "status": status})
        self.send_response(status)
        sent_length = False
        for key, value in response_headers:
            if key.lower() in {"connection", "transfer-encoding", "content-encoding"}:
                continue
            if key.lower() == "content-length":
                sent_length = True
            self.send_header(key, value)
        if not sent_length:
            self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path.startswith(("/api/", "/media/")):
            self._proxy()
            return
        candidate = DIST / urlsplit(self.path).path.lstrip("/")
        if not candidate.is_file() and not candidate.is_dir():
            self.path = "/index.html"
        super().do_GET()

    def do_HEAD(self) -> None:
        if self.path.startswith(("/api/", "/media/")):
            self._proxy()
            return
        super().do_HEAD()

    def do_POST(self) -> None:
        self._proxy()

    def do_PUT(self) -> None:
        self._proxy()

    def do_PATCH(self) -> None:
        self._proxy()

    def do_DELETE(self) -> None:
        self._proxy()


class WebDriver:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.root = f"/session/{session_id}"

    @staticmethod
    def request(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
        connection = http.client.HTTPConnection("127.0.0.1", GECKO_PORT, timeout=timeout)
        encoded = json.dumps(payload).encode() if payload is not None else None
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        try:
            connection.request(method, path, body=encoded, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            status = response.status
        finally:
            connection.close()
        value = json.loads(raw) if raw else {}
        response_value = value.get("value") if isinstance(value, dict) else None
        if status >= 400 or (isinstance(response_value, dict) and response_value.get("error")):
            raise BrowserFailure(f"WebDriver {method} {path} returned {status}: {value}")
        return value

    def command(self, method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> Any:
        return self.request(method, self.root + path, payload, timeout).get("value")

    def script(self, source: str, args: list[Any] | None = None) -> Any:
        return self.command("POST", "/execute/sync", {"script": source, "args": args or []}, timeout=45)

    def element(self, using: str, locator: str) -> str:
        result = self.command("POST", "/element", {"using": using, "value": locator})
        return result[ELEMENT_KEY]

    def maybe_element(self, using: str, locator: str) -> str | None:
        try:
            return self.element(using, locator)
        except BrowserFailure:
            return None

    def click(self, element_id: str) -> None:
        self.command("POST", f"/element/{element_id}/click", {})

    def send_keys(self, element_id: str, value: str) -> None:
        state = self.script(
            "const e=arguments[0];e.scrollIntoView({block:'center'});e.focus();return {tag:e.tagName,disabled:e.disabled,rect:e.getBoundingClientRect().toJSON()};",
            [{ELEMENT_KEY: element_id}],
        )
        if state["disabled"]:
            raise BrowserFailure(f"Cannot type into disabled {state['tag']} element: {state['rect']}")
        self.command("POST", f"/element/{element_id}/value", {"text": value, "value": list(value)})

    def clear(self, element_id: str) -> None:
        self.command("POST", f"/element/{element_id}/clear", {})

    def screenshot(self, destination: Path) -> None:
        data = self.command("GET", "/screenshot")
        destination.write_bytes(base64.b64decode(data))


def wait_until(driver: WebDriver, script: str, description: str, seconds: int = 30, args: list[Any] | None = None) -> Any:
    deadline = time.monotonic() + seconds
    last: Any = None
    while time.monotonic() < deadline:
        last = driver.script(script, args)
        if last:
            return last
        time.sleep(0.25)
    raise BrowserFailure(f"Timed out waiting for {description}; last={last!r}")


def wait_text(driver: WebDriver, text: str, seconds: int = 30) -> None:
    wait_until(driver, "return document.body && document.body.innerText.includes(arguments[0])", f"text {text!r}", seconds, [text])


def xpath_button(driver: WebDriver, label: str) -> str:
    escaped = label.replace("'", "&apos;")
    return driver.element("xpath", f"//button[normalize-space(.)='{escaped}']")


def click_button(driver: WebDriver, label: str) -> None:
    element_id = xpath_button(driver, label)
    driver.script("arguments[0].scrollIntoView({block:'center'});", [{ELEMENT_KEY: element_id}])
    driver.click(element_id)


def select_value(driver: WebDriver, selector: str, value: str) -> None:
    result = driver.script(
        "const e=document.querySelector(arguments[0]); if(!e) return false; e.value=arguments[1]; e.dispatchEvent(new Event('change',{bubbles:true})); return true;",
        [selector, value],
    )
    if not result:
        raise BrowserFailure(f"Unable to select {value!r} in {selector}")


def make_png(destination: Path) -> None:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return len(payload).to_bytes(4, "big") + kind + payload + (zlib.crc32(kind + payload) & 0xFFFFFFFF).to_bytes(4, "big")

    width = height = 8
    rows = b"".join(b"\x00" + bytes([48, 132, 82, 255]) * width for _ in range(height))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", width.to_bytes(4, "big") + height.to_bytes(4, "big") + bytes([8, 6, 0, 0, 0]))
    png += chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")
    destination.write_bytes(png)


def main() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    profile_root = TMP / "firefox-profile-root"
    profile_root.mkdir(exist_ok=True)
    photo = TMP / "quality-package.png"
    make_png(photo)
    proxy = http.server.ThreadingHTTPServer(("127.0.0.1", FRONTEND_PORT), ProxyHandler)
    proxy.api_calls = []
    proxy_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
    proxy_thread.start()
    gecko = subprocess.Popen(
        [str(GECKODRIVER), "--host", "127.0.0.1", "--port", str(GECKO_PORT), "--profile-root", str(profile_root), "--binary", "/usr/bin/firefox", "--log", "error"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    driver: WebDriver | None = None
    report: dict[str, Any] = {
        "browser": "Firefox 136.0 headless through Mozilla geckodriver 0.37.1",
        "frontend_origin": BASE_URL,
        "isolated_backend_origin": BACKEND_URL,
        "isolated_database": str(TMP / "business.sqlite3"),
        "journey_steps": [],
        "checks": {},
    }
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{GECKO_PORT}/status", timeout=1) as response:
                    if response.status == 200:
                        break
            except (OSError, urllib.error.URLError):
                time.sleep(0.25)
        else:
            raise BrowserFailure("geckodriver did not become ready")

        created = WebDriver.request("POST", "/session", {
            "capabilities": {"alwaysMatch": {
                "browserName": "firefox",
                "moz:firefoxOptions": {"binary": "/usr/bin/firefox", "args": ["-headless"]},
            }},
        }, timeout=60)
        session_id = created["value"]["sessionId"]
        driver = WebDriver(session_id)
        driver.command("POST", "/window/rect", {"width": 1440, "height": 1000, "x": 0, "y": 0})
        driver.command("POST", "/url", {"url": BASE_URL})
        wait_text(driver, "Ceres的朋友")
        report["journey_steps"].append("opened Ceres landing page in isolated native Firefox")

        click_button(driver, "商品")
        search = driver.element("css selector", 'input[placeholder="搜索有机食材与好物"]')
        driver.send_keys(search, "虾仁")
        wait_until(driver, "return [...document.querySelectorAll('article')].some(e=>e.innerText.includes('虾仁'))", "hybrid shrimp product card", 60)
        product_name = driver.script("return [...document.querySelectorAll('article')].find(e=>e.innerText.includes('虾仁'))?.innerText || null")
        report["checks"]["retrieval_rendered_shrimp_product"] = bool(product_name)
        report["journey_steps"].append("searched the 71-SKU demo catalog for shrimp and opened a rendered result")
        details = driver.element("xpath", "//button[starts-with(@aria-label,'查看') and contains(@aria-label,'详情')]")
        driver.click(details)
        wait_until(driver, "return !!document.querySelector('[role=dialog][aria-label=\"商品详情\"] button') && document.body.innerText.includes('添加一件到购物车')", "product detail")
        click_button(driver, "添加一件到购物车")
        wait_until(driver, "return [...document.querySelectorAll('button[aria-label]')].some(e=>e.getAttribute('aria-label')==='购物车' && e.innerText.trim()!=='') || document.body.innerText.includes('已加入') || document.querySelector('[role=dialog][aria-label=\"商品详情\"]')", "cart addition", 20)
        report["journey_steps"].append("opened product detail and added one item to cart")
        close_detail = driver.element("xpath", "//*[@role='dialog' and @aria-label='商品详情']//button[normalize-space(.)='关闭']")
        driver.click(close_detail)
        driver.click(driver.element("css selector", 'button[aria-label="购物车"]'))
        wait_until(driver, "return !!document.querySelector('[role=dialog][aria-label=\"购物车\"]')", "cart drawer")
        cart_text = driver.script("return document.querySelector('[role=dialog][aria-label=\"购物车\"]')?.innerText || ''")
        if "虾仁" not in cart_text:
            raise BrowserFailure(f"Cart did not contain the selected shrimp product: {cart_text!r}")
        click_button(driver, "模拟结算")
        wait_until(driver, "return !!document.querySelector('[role=dialog][aria-label=\"模拟结算\"]')", "simulated checkout")
        click_button(driver, "确认模拟结算")
        wait_text(driver, "模拟订单已保存", 30)
        order_id = driver.script("return document.querySelector('[role=dialog][aria-label=\"模拟结算\"]')?.innerText.match(/order-[a-f0-9-]+/i)?.[0] || null")
        click_button(driver, "查看订单")
        wait_text(driver, "我的模拟订单")
        order_row = driver.element("xpath", "//button[starts-with(@aria-label,'查看订单')]")
        driver.click(order_row)
        wait_until(driver, "return !!document.querySelector('[data-order-id]')", "order detail")
        order_id = driver.script("return document.querySelector('[data-order-id]')?.getAttribute('data-order-id')") or order_id
        report["checks"]["simulated_order_created"] = bool(order_id)
        report["journey_steps"].append("completed demo checkout and opened its immutable order snapshot")

        click_button(driver, "模拟推进至配送中")
        wait_text(driver, "shipped", 15)
        click_button(driver, "模拟签收")
        wait_until(driver, "return document.querySelector('[data-order-id]')?.innerText.includes('delivered')", "delivered order state")
        report["checks"]["order_state_submitted_to_shipped_to_delivered"] = True
        report["journey_steps"].append("advanced order through submitted → shipped → delivered in the UI")
        click_button(driver, "联系墨墨")
        wait_until(driver, "return !!document.querySelector('select[aria-label=\"售后类型\"]')", "Momo aftersales form", 45)
        wait_until(driver, "return document.querySelector('[data-selected-order-id]')?.getAttribute('data-selected-order-id') === arguments[0]", "selected order in Momo", 20, [order_id])
        report["journey_steps"].append("entered Momo with the selected delivered order")

        select_value(driver, 'select[aria-label="售后类型"]', "quality")
        wait_until(driver, "return !!document.querySelector('select[aria-label=\"退货商品\"]')", "quality item selector")
        select_value(driver, 'select[aria-label="退货商品"]', "demo:shrimp-200g")
        quantity = driver.element("css selector", 'input[aria-label="问题销售包装数"]')
        driver.send_keys(quantity, "1")
        file_input = driver.element("css selector", 'input[aria-label="质量问题照片"]')
        driver.send_keys(file_input, str(photo))
        wait_until(driver, "return !!document.querySelector('input[aria-label=\"售后原因\"]') && !document.querySelector('input[aria-label=\"售后原因\"]').disabled", "photo upload completion and form re-enable", 20)
        reason = driver.element("css selector", 'input[aria-label="售后原因"]')
        driver.send_keys(reason, "签收时发现销售包装破损（Firefox浏览器演示）")
        wait_until(driver, "return [...document.querySelectorAll('img[alt=\"待人工核对的照片\"]')].length===1", "uploaded quality photo preview", 20)
        click_button(driver, "查看申请提案")
        wait_text(driver, "待确认：质量问题登记", 30)
        wait_until(driver, "return !!document.querySelector('img[alt=\"此提案关联的待核对照片\"]')", "proposal-bound photo preview")
        proposal_text = driver.script("return document.querySelector('[data-proposal-id]')?.innerText || ''")
        report["checks"]["quality_proposal_has_one_package_and_photo"] = "× 1" in proposal_text and bool(driver.script("return document.querySelector('img[alt=\"此提案关联的待核对照片\"]')"))
        click_button(driver, "确认提交此模拟申请")
        wait_text(driver, "模拟申请已提交", 30)
        receipt_text = driver.script("return [...document.querySelectorAll('[data-receipt-id]')].map(e=>e.innerText).join('\\n')")
        report["checks"]["quality_application_confirmed_with_photo"] = "模拟申请已提交" in receipt_text and report["checks"]["quality_proposal_has_one_package_and_photo"]
        report["checks"]["receipt"] = receipt_text
        report["journey_steps"].append("uploaded a PNG, reviewed a photo-bound quality proposal, and confirmed the application")

        driver.command("POST", "/url", {"url": BASE_URL + "/operator/human-cases"})
        wait_text(driver, "模拟售后 · 异步人工工单")
        token_input = driver.element("css selector", 'input[type="password"]')
        driver.send_keys(token_input, OPERATOR_TOKEN)
        click_button(driver, "读取 / 刷新工单")
        wait_until(driver, "return !!document.querySelector('section[aria-label=\"工单列表\"] button')", "operator ticket list", 30)
        ticket = driver.element("css selector", 'section[aria-label="工单列表"] button')
        ticket_summary = driver.script("return arguments[0].innerText", [{ELEMENT_KEY: ticket}])
        driver.click(ticket)
        wait_text(driver, "问题销售包装数 1", 20)
        wait_until(driver, "return !!document.querySelector('section[aria-label=\"工单详情\"] img[alt=\"待核对的问题照片\"]')", "operator-scoped photo view", 30)
        report["checks"]["operator_can_read_quality_ticket_and_photo"] = True
        report["checks"]["operator_ticket_summary"] = ticket_summary
        report["checks"]["operator_view_contains_photo"] = True
        report["journey_steps"].append("operator UI authenticated with the isolated test token and viewed the matching ticket photo")
        screenshot = TMP / "browser-demo-journey.png"
        driver.screenshot(screenshot)
        report["screenshot"] = str(screenshot)
        report["proxy_api_calls"] = proxy.api_calls
        boolean_checks = [value for value in report["checks"].values() if isinstance(value, bool)]
        report["checks"]["all_boolean_checks_passed"] = all(boolean_checks)
        report["result"] = "passed" if report["checks"]["all_boolean_checks_passed"] else "failed"
    except Exception as error:
        report["result"] = "failed"
        report["error"] = str(error)
        report["traceback"] = traceback.format_exc()
        report["proxy_api_calls"] = proxy.api_calls
        if driver is not None:
            try:
                report["failure_page_text"] = driver.script("return document.body?.innerText.slice(-5000) || ''")
                failure_screenshot = TMP / "browser-demo-failure.png"
                driver.screenshot(failure_screenshot)
                report["failure_screenshot"] = str(failure_screenshot)
            except Exception:
                pass
    finally:
        if driver is not None:
            try:
                driver.request("DELETE", f"/session/{driver.session_id}", timeout=10)
            except Exception:
                pass
        proxy.shutdown()
        proxy.server_close()
        gecko.terminate()
        try:
            gecko.wait(timeout=10)
        except subprocess.TimeoutExpired:
            gecko.kill()
    output = TESTING / "browser-demo-journey-2026-10-07.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["result"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
