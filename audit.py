# -*- coding: utf-8 -*-
"""
HA-Digital-Portfolio / tools/audit.py
------------------------------------------------------------------
أداة فحص بصري ووظيفي للموقع تعمل عبر Chrome في وضع headless:
  1. التقاط لقطات شاشة بأحجام شاشات مختلفة (Desktop / Laptop / Tablet / Mobile).
  2. التقاط لقطة كاملة للصفحة (Full Page).
  3. التقاط نسخة مطبوعة (Print to PDF) للتحقق من تنسيق تصدير PDF.
  4. فحص أخطاء JavaScript في الـ Console.
  5. التحقق من تحميل كل الصور والخطوط.
  6. التحقق من عدم وجود تمرير أفقي غير مقصود.
  7. التحقق من عمل عناصر الواجهة الأساسية (القائمة، الوضع الليلي، النافذة المنبثقة).

التشغيل:  python tools/audit.py
"""

import json
import os
import subprocess
import sys
import time
import urllib.request

from PIL import Image

# ضبط ترتيب الإخراج إلى UTF-8 حتى تظهر النصوص العربية بشكل صحيح
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "tools", "shots")
os.makedirs(SHOTS, exist_ok=True)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "http://127.0.0.1:8777/index.html"

VIEWPORTS = [
    ("desktop-1440", 1440, 900),
    ("laptop-1280", 1280, 800),
    ("tablet-820", 820, 1180),
    ("mobile-390", 390, 844),
]


def chrome_args(port, width, height, extra=None):
    profile = os.path.join(
        os.environ.get("TEMP", "C:\\Windows\\Temp"),
        "opencode", "ha-cdp-%d" % port)
    os.makedirs(profile, exist_ok=True)
    args = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-extensions-except=",
        "--disable-background-networking",
        "--user-data-dir=%s" % profile,
        "--force-device-scale-factor=1",
        "--remote-debugging-port=%d" % port,
        "--window-size=%d,%d" % (width, height),
    ]
    if extra:
        args.extend(extra)
    args.append(URL)
    return args


def cdp(port, path, method="GET", body=None, timeout=30):
    """طلب بسيط عبر بروتوكول Chrome DevTools."""
    import urllib.request as u
    url = "http://127.0.0.1:%d%s" % (port, path)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req = u.Request(url, data=data, method=method,
                        headers={"Content-Type": "application/json"})
    else:
        req = u.Request(url, method=method)
    with u.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", "replace")
    return json.loads(raw) if raw.strip() else {}


def run_chrome(port, width, height, extra=None):
    proc = subprocess.Popen(
        chrome_args(port, width, height, extra),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # انتظار جاهزية منفذ التصحيح
    ready = False
    for _ in range(80):
        try:
            cdp(port, "/json/version", timeout=2)
            ready = True
            break
        except Exception:
            time.sleep(0.35)
    if not ready:
        print("  [!!] تعذّر تشغيل Chrome على المنفذ %d" % port)
    return proc


class Session(object):
    """جلسة CDP مصغّرة."""

    def __init__(self, port):
        self.port = port
        self.ws = None
        self.msg_id = 0
        self.messages = []

    def connect(self):
        import socket
        import base64
        import os as _os

        page = None
        for _attempt in range(40):
            try:
                targets = cdp(self.port, "/json/list")
            except Exception:
                targets = []
            for target in targets:
                if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                    page = target
                    break
            if page:
                break
            time.sleep(0.4)
        if page is None:
            raise RuntimeError("لا يوجد هدف صفحة")

        url = page["webSocketDebuggerUrl"]
        # استخراج المسار فقط من رابط ws://
        path = "/" + url.split("://", 1)[1].split("/", 1)[1]
        host = page.get("host", "127.0.0.1")
        ws_port = page.get("port", self.port)

        # الحد الأدنى من عميل WebSocket (بدون مكتبات خارجية)
        self.sock = socket.create_connection((host, ws_port), timeout=30)
        key = base64.b64encode(_os.urandom(16)).decode()
        handshake = (
            "GET %s HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\n"
            "Connection: Upgrade\r\nSec-WebSocket-Key: %s\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
            % (path, host, ws_port, key)
        )
        self.sock.sendall(handshake.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("فشل مصافحة WebSocket")
            buf += chunk
        header, self._rest = buf.split(b"\r\n\r\n", 1)
        if b"101" not in header.split(b"\r\n")[0]:
            raise RuntimeError("رفض الخادم مصافحة WebSocket: %s" % header[:120])

    # --- إطارات WebSocket ---
    def _read_more(self):
        """قراءة المزيد من البايتات إلى المخزن المؤقت."""
        if self._rest:
            return True
        try:
            chunk = self.sock.recv(65536)
        except Exception:
            return False
        if not chunk:
            return False
        self._rest = chunk
        return True

    def _recv_exact(self, n):
        """قراءة n بايت بالضبط من المخزن المؤقت."""
        while len(self._rest) < n:
            if not self._read_more():
                raise RuntimeError("انقطع الاتصال")
        data, self._rest = self._rest[:n], self._rest[n:]
        return data

    def _send(self, payload):
        data = json.dumps(payload).encode("utf-8")
        header = bytearray([0x81])
        mask = os.urandom(4)
        length = len(data)
        if length < 126:
            header.append(0x80 | length)
        elif length < (1 << 16):
            header.append(0x80 | 126)
            header += length.to_bytes(2, "big")
        else:
            header.append(0x80 | 127)
            header += length.to_bytes(8, "big")
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self.sock.sendall(bytes(header) + masked)

    def _read_frame(self):
        head = self._recv_exact(2)
        fin = head[0] & 0x80
        opcode = head[0] & 0x0F
        masked = head[1] & 0x80
        length = head[1] & 0x7F
        if length == 126:
            length = int.from_bytes(self._recv_exact(2), "big")
        elif length == 127:
            length = int.from_bytes(self._recv_exact(8), "big")
        mask = self._recv_exact(4) if masked else None
        payload = self._recv_exact(length) if length else b""
        if mask:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        if opcode == 0x8:
            raise RuntimeError("أُغلق الاتصال")
        return fin, opcode, payload

    def _read_message(self):
        """قراءة رسالة كاملة مع دعم تجزّؤ الإطارات (fragmentation) و ping/pong."""
        chunks = []
        while True:
            fin, opcode, payload = self._read_frame()
            if opcode == 0x9:      # ping
                self._send_raw(0xA, payload)
                continue
            if opcode == 0xA:      # pong
                continue
            chunks.append(payload)
            if fin:
                return b"".join(chunks)

    def _send_raw(self, opcode, payload):
        data = payload
        header = bytearray([0x80 | opcode])
        mask = os.urandom(4)
        length = len(data)
        if length < 126:
            header.append(0x80 | length)
        elif length < (1 << 16):
            header.append(0x80 | 126)
            header += length.to_bytes(2, "big")
        else:
            header.append(0x80 | 127)
            header += length.to_bytes(8, "big")
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self.sock.sendall(bytes(header) + masked)

    def command(self, method, params=None, timeout=40):
        self.msg_id += 1
        mid = self.msg_id
        self._send({"id": mid, "method": method, "params": params or {}})

        deadline = time.time() + timeout
        while time.time() < deadline:
            payload = self._read_message()
            msg = json.loads(payload.decode("utf-8"))
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError("%s -> %s" % (method, msg["error"]))
                return msg.get("result", {})
            self.messages.append(msg)
        raise RuntimeError("انتهت المهلة في %s" % method)

    def evaluate(self, expression, timeout=40):
        result = self.command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
        }, timeout=timeout)
        if result.get("exceptionDetails"):
            raise RuntimeError(str(result["exceptionDetails"].get("text")))
        return result.get("result", {}).get("value")

    def freeze_animations(self):
        """تجميد الحركات وإظهار عناصر الظهور للحصول على لقطة ثابتة."""
        self.evaluate("""(function(){
            var style = document.createElement('style');
            style.id = 'audit-freeze';
            style.textContent = '*,*::before,*::after{animation-play-state:paused !important;transition:none !important;}'
                + '.reveal{opacity:1 !important;transform:none !important;}'
                + '.hero__caret{opacity:1 !important;}';
            document.head.appendChild(style);
            window.scrollTo(0,0);
            return true;
        })()""")
        time.sleep(0.8)

    def screenshot(self, path, full_page=False):
        if full_page:
            metrics = self.command("Page.getLayoutMetrics")
            size = metrics.get("cssContentSize") or metrics.get("contentSize")
            width = int(size["width"])
            height = min(int(size["height"]), 15000)

            # توسيع إطار العرض ليطابق الصفحة كاملة ثم التقاط
            self.command("Emulation.setDeviceMetricsOverride", {
                "width": width, "height": height,
                "deviceScaleFactor": 1, "mobile": False})
            time.sleep(1.2)

            data = self.command("Page.captureScreenshot", {"format": "png"}, timeout=120)
            with open(path, "wb") as handle:
                handle.write(base64.b64decode(data["data"]))

            # استعادة المقاس الأصلي
            self.command("Emulation.setDeviceMetricsOverride", {
                "width": 1440, "height": 900,
                "deviceScaleFactor": 1, "mobile": False})
            return path

        data = self.command("Page.captureScreenshot", {"format": "png"}, timeout=90)
        with open(path, "wb") as handle:
            handle.write(base64.b64decode(data["data"]))
        return path

    def pdf(self, path, landscape=False):
        data = self.command("Page.printToPDF", {
            "printBackground": True,
            "preferCSSPageSize": True,
            "landscape": landscape,
            "marginTop": 0.5, "marginBottom": 0.5,
            "marginLeft": 0.5, "marginRight": 0.5,
        }, timeout=90)
        with open(path, "wb") as handle:
            handle.write(base64.b64decode(data["data"]))
        return path


def cli_capture(output_path, width, height, pdf=False, url=None):
    """
    التقاط عبر واجهة سطر الأوامر في Chrome.
    الوضع headless الجديد في الإصدارات الحديثة من Chrome لا يستجيب
    لطلب Page.captureScreenshot عبر CDP، لذا نستخدم الأداة الأصلية.
    ملاحظة: Chrome في وضع headless يفرض حدًا أدنى لعرض النافذة (~500px)،
    لذلك نستخدم صفحة غلاف بإطار iframe للعرضات الضيقة.
    """
    profile = os.path.join(
        os.environ.get("TEMP", "C:\\Windows\\Temp"),
        "opencode", "ha-cli-%d" % (abs(hash(output_path)) % 99991))
    os.makedirs(profile, exist_ok=True)

    args = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--force-device-scale-factor=1",
        "--user-data-dir=%s" % profile,
        "--window-size=%d,%d" % (width, height),
    ]

    target = url or (URL + "?static=1")

    if not pdf and width < 500:
        # عرض دقيق عبر iframe بعرض الجوال الحقيقي
        frame = os.path.join(ROOT, "tools", "mobile-frame.html")
        target = "file:///" + frame.replace("\\", "/")
        args.append("--window-size=500,%d" % height)

    if pdf:
        args.append("--no-pdf-header-footer")
        args.append("--print-to-pdf=%s" % output_path)
    else:
        args.append("--screenshot=%s" % output_path)

    args.append(target)

    subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)

    if not pdf and width < 500 and os.path.exists(output_path):
        # قصّ الصورة إلى العرض المطلوب
        from PIL import Image
        image = Image.open(output_path)
        if image.width > width:
            image.crop((0, 0, width, min(height, image.height))).save(output_path)
        image.close()

    return output_path if os.path.exists(output_path) else None


def cli_fullpage_capture(output_path, width, url=None):
    """
    التقاط الصفحة كاملة.

    ملاحظة: الواجهة الرئيسية تستخدم min-height:100vh، لذلك عند تكبير
    النافذة become الهيرو عملاقًا. نستخدم نسخة معاينة بستايل مؤقت
    يضغط الهيرو ليصبح تدفق الصفحة طبيعيًا ثم نلتقط الصفحة كاملة.
    """
    preview = os.path.join(ROOT, "_preview_fullpage.html")
    with open(os.path.join(ROOT, "index.html"), "r", encoding="utf-8") as handle:
        html = handle.read()

    override = (
        "<style>"
        ".hero{min-height:auto!important;padding-block:120px 70px!important}"
        ".scene{position:absolute}"
        "</style></head>"
    )
    html = html.replace("</head>", override, 1)
    with open(preview, "w", encoding="utf-8") as handle:
        handle.write(html)

    try:
        target = "http://127.0.0.1:8777/_preview_fullpage.html?static=1"
        if url and "lang=en" in url:
            target = "http://127.0.0.1:8777/_preview_fullpage.html?static=1&lang=en"
        return cli_capture(output_path, width, 12000, url=target)
    finally:
        try:
            os.remove(preview)
        except OSError:
            pass


def main():
    report = {"checks": [], "errors": [], "screens": []}

    def check(name, ok, detail=""):
        report["checks"].append({"name": name, "ok": bool(ok), "detail": str(detail)})
        print("  %s  %-52s %s" % ("PASS" if ok else "FAIL", name, detail))

    port = 9333
    print("=" * 74)
    print("  HA-Digital-Portfolio | الفحص البصري والوظيفي")
    print("=" * 74)

    proc = run_chrome(port, 1440, 900)
    session = Session(port)
    try:
        session.connect()
        session.command("Page.enable")
        session.command("Runtime.enable")
        session.command("Log.enable")
        session.command("Emulation.setDeviceMetricsOverride", {
            "width": 1440, "height": 900, "deviceScaleFactor": 1, "mobile": False})
        session.command("Page.navigate", {"url": URL})
        time.sleep(4)

        # ---------- أخطاء الـ Console ----------
        print("\n-- أخطاء JavaScript --")
        errors = []
        for msg in session.messages:
            if msg.get("method") == "Runtime.exceptionThrown":
                errors.append(str(msg["params"]["exceptionDetails"].get("text")))
            if msg.get("method") == "Log.entryAdded":
                entry = msg["params"]["entry"]
                if entry.get("level") == "error":
                    errors.append(entry.get("text", ""))
        report["errors"] = errors
        check("لا توجد أخطاء JavaScript", len(errors) == 0, "; ".join(errors[:3]))

        # ---------- تحميل الصور ----------
        print("\n-- الأصول --")
        assets = session.evaluate("""(function(){
            var imgs = Array.prototype.slice.call(document.images);
            var broken = imgs.filter(function(i){
                var src = i.getAttribute('src');
                if (!src) return false;                 // صور بدون مصدر (مثل نافذة المشروع قبل فتحها)
                return i.complete && i.naturalWidth === 0;
            }).map(function(i){ return i.getAttribute('src'); });
            return {total: imgs.length, broken: broken,
                    fontsLoaded: document.fonts ? document.fonts.status : 'unsupported'};
        })()""")
        check("كل الصور تحمّل بنجاح", len(assets["broken"]) == 0, assets["broken"])
        check("عدد الصور", assets["total"] >= 8, "%d صورة" % assets["total"])
        check("الخطوط جاهزة", assets["fontsLoaded"] in ("loaded", "loading"), assets["fontsLoaded"])

        # ---------- التمرير الأفقي ----------
        overflow = session.evaluate("""(function(){
            return {doc: document.documentElement.scrollWidth, win: window.innerWidth,
                    over: document.documentElement.scrollWidth - window.innerWidth};
        })()""")
        check("لا يوجد تمرير أفقي (1440px)", overflow["over"] <= 1,
              "فرق=%dpx" % overflow["over"])

        # ---------- عناصر الواجهة ----------
        print("\n-- عناصر الواجهة --")
        ui = session.evaluate("""(function(){
            return {
                navLinks: document.querySelectorAll('.nav__link').length,
                sections: document.querySelectorAll('main section').length,
                projectCards: document.querySelectorAll('.project').length,
                skillItems: document.querySelectorAll('.skill').length,
                pCards: document.querySelectorAll('.p-card').length,
                interests: document.querySelectorAll('.interest').length,
                revealTotal: document.querySelectorAll('.reveal').length,
                revealVisible: document.querySelectorAll('.reveal.is-visible').length,
                typed: (document.getElementById('typedRole')||{}).textContent || '',
                theme: document.documentElement.getAttribute('data-theme'),
                year: (document.getElementById('currentYear')||{}).textContent || '',
                h1: Array.prototype.map.call(document.querySelectorAll('h1'), function(h){return h.textContent.trim();}),
                h2: document.querySelectorAll('h2').length,
                h3: document.querySelectorAll('h3').length,
                imgsNoAlt: Array.prototype.filter.call(document.images, function(i){return !i.hasAttribute('alt');}).length,
                btnsNoName: Array.prototype.filter.call(document.querySelectorAll('button'), function(b){
                    return !b.textContent.trim() && !b.getAttribute('aria-label') && !b.getAttribute('title');}).length,
                emptyHref: Array.prototype.filter.call(document.querySelectorAll('a'), function(a){
                    var h=a.getAttribute('href'); return h===''||h==='#'||h==='javascript:void(0)';}).length,
                i18nNodes: document.querySelectorAll('[data-i18n]').length,
                langOpts: document.querySelectorAll('[data-lang-opt]').length
            };
        })()""")
        check("روابط التنقل (9)", ui["navLinks"] == 9, ui["navLinks"])
        check("أقسام الصفحة (9)", ui["sections"] == 9, ui["sections"])
        check("بطاقات المشاريع (5)", ui["projectCards"] == 5, ui["projectCards"])
        check("عناصر المهارات (17)", ui["skillItems"] == 17, ui["skillItems"])
        check("بطاقات الشخصية (4)", ui["pCards"] == 4, ui["pCards"])
        check("المجالات (7)", ui["interests"] == 7, ui["interests"])
        check("عنوان H1 واحد فقط", len(ui["h1"]) == 1, ui["h1"])
        check("كل الصور لها نص بديل", ui["imgsNoAlt"] == 0, ui["imgsNoAlt"])
        check("كل الأزرار لها تسمية", ui["btnsNoName"] == 0, ui["btnsNoName"])
        check("لا توجد روابط فارغة", ui["emptyHref"] == 0, ui["emptyHref"])
        check("عناصر قابلة للترجمة (200+)",
              ui["i18nNodes"] >= 200, "%d عنصر" % ui["i18nNodes"])
        check("خيارا اللغة موجودان", ui["langOpts"] == 2, ui["langOpts"])
        check("نص الكتابة المتحرك يعمل", len(ui["typed"]) > 20, ui["typed"][:46])
        check("السنة الحالية صحيحة", ui["year"] == str(__import__("datetime").datetime.now().year), ui["year"])

        # ---------- روابط التواصل ----------
        links = session.evaluate("""(function(){
            return {
                wa: (document.querySelector('a[href*="wa.me"]')||{}).href || '',
                tel: (document.querySelector('a[href^="tel:"]')||{}).href || '',
                mail: (document.querySelector('a[href^="mailto:"]')||{}).href || ''
            };
        })()""")
        check("رابط واتساب صحيح", links["wa"] == "https://wa.me/966557123774", links["wa"])
        check("رابط الاتصال صحيح", links["tel"] == "tel:+966557123774", links["tel"])
        check("رابط البريد صحيح", links["mail"] == "mailto:lcf277940@gmail.com", links["mail"])

        # ---------- التبديل بين اللغتين ----------
        print("\n-- تعدد اللغات --")
        session.evaluate("""document.querySelector('[data-lang-opt="en"]').click()""")
        time.sleep(1.2)
        en = session.evaluate("""(function(){
            var root = document.documentElement;
            return {
                lang: root.getAttribute('lang'), dir: root.getAttribute('dir'),
                nav1: document.querySelector('.nav__link').textContent.trim(),
                title: document.querySelector('.hero__title').textContent.replace(/\\s+/g,' ').trim(),
                contact: document.querySelector('.contact__whatsapp-title').textContent.trim().slice(0,30),
                docTitle: document.title,
                stored: window.localStorage.getItem('ha-portfolio-lang'),
                over: document.documentElement.scrollWidth - window.innerWidth
            };
        })()""")
        check("تحويل lang إلى en", en["lang"] == "en", en["lang"])
        check("تحويل dir إلى ltr", en["dir"] == "ltr", en["dir"])
        check("ترجمة شريط التنقل", en["nav1"] == "Home", en["nav1"])
        check("ترجمة اسم العنوان", "Hadeel" in en["title"], en["title"])
        check("ترجمة عنوان الصفحة", en["docTitle"].startswith("Hadeel"), en["docTitle"][:34])
        check("ترجمة قسم التواصل", "glad" in en["contact"], en["contact"])
        check("حفظ اللغة في LocalStorage", en["stored"] == "en", en["stored"])
        check("لا تمرير أفقي بالإنجليزية", en["over"] <= 1, "فرق=%dpx" % en["over"])

        session.evaluate("""document.querySelector('[data-lang-opt="ar"]').click()""")
        time.sleep(1.0)
        ar = session.evaluate("""(function(){
            return {lang: document.documentElement.getAttribute('lang'),
                    dir: document.documentElement.getAttribute('dir'),
                    nav1: document.querySelector('.nav__link').textContent.trim(),
                    title: document.querySelector('.hero__title').textContent.replace(/\\s+/g,' ').trim()};
        })()""")
        check("العودة إلى العربية", ar["lang"] == "ar" and ar["dir"] == "rtl",
              "%s / %s" % (ar["lang"], ar["dir"]))
        check("استعادة النص العربي", ar["nav1"] == "الرئيسية", ar["nav1"])
        check("استعادة الاسم العربي", "هديل" in ar["title"], ar["title"])

        # ---------- الوضع الليلي ----------
        print("\n-- المزايا التفاعلية --")
        session.evaluate("document.getElementById('themeToggle').click()")
        time.sleep(0.6)
        dark = session.evaluate("document.documentElement.getAttribute('data-theme')")
        stored = session.evaluate("window.localStorage.getItem('ha-portfolio-theme')")
        check("تبديل الوضع الليلي", dark == "dark", dark)
        check("حفظ التفضيل في LocalStorage", stored == "dark", stored)

        session.evaluate("document.getElementById('themeToggle').click()")
        time.sleep(0.4)
        light = session.evaluate("document.documentElement.getAttribute('data-theme')")
        check("العودة للوضع النهاري", light == "light", light)

        # ---------- النافذة المنبثقة ----------
        session.evaluate("""document.querySelector('[data-open-project="1"]').click()""")
        time.sleep(0.6)
        modal = session.evaluate("""(function(){
            var m = document.getElementById('projectModal');
            return {hidden: m.hidden, title: document.getElementById('modalTitle').textContent.trim(),
                    content: document.getElementById('modalContent').textContent.length};
        })()""")
        check("فتح نافذة تفاصيل المشروع", modal["hidden"] is False and modal["content"] > 80,
              modal["title"][:40])
        session.evaluate("document.getElementById('modalClose').click()")
        time.sleep(0.4)
        check("إغلاق النافذة", session.evaluate("document.getElementById('projectModal').hidden") is True)

        # ---------- التمرير والقسم النشط ----------
        session.evaluate("window.scrollTo(0, document.getElementById('projects').offsetTop)")
        time.sleep(1.2)
        active = session.evaluate("""(function(){
            var a = document.querySelector('.nav__link.is-active');
            var ind = document.getElementById('navIndicator');
            return {text: a ? a.textContent.trim() : '', w: ind ? ind.style.width : '0px',
                    op: ind ? ind.style.opacity : '0'};
        })()""")
        check("تحديد القسم النشط عند التمرير", active["text"] == "المشاريع", active["text"])
        check("ظهور مؤشر شريط التنقل", active["w"] not in ("", "0px"), active["w"])

        # ---------- شريط تقدم القراءة ----------
        progress = session.evaluate("document.getElementById('readingProgress').style.width")
        check("شريط تقدم القراءة يعمل", progress not in ("", "0%"), progress)

        # ---------- زر العودة للأعلى ----------
        btt = session.evaluate("document.getElementById('backToTop').classList.contains('is-visible')")
        check("ظهور زر العودة للأعلى", btt is True)

        # ---------- قياس ارتفاع الصفحة ----------
        page_height = session.evaluate("document.documentElement.scrollHeight")
        print("  ارتفاع الصفحة: %dpx" % page_height)

    finally:
        try:
            proc.terminate()
        except Exception:
            pass

    # ---------- التقاط الشاشات عبر CLI ----------
    print("\n-- اللقطات --")
    shots = [
        ("desktop-hero.png", 1440, 900),
        ("laptop-1280.png", 1280, 800),
        ("tablet-820.png", 820, 1180),
        ("mobile-390.png", 390, 844),
    ]
    for name, width, height in shots:
        path = os.path.join(SHOTS, name)
        result = cli_capture(path, width, height)
        ok = result is not None
        check("لقطة %s (%dx%d)" % (name, width, height), ok,
              "%.0f KB" % (os.path.getsize(path) / 1024.0) if ok else "فشل")
        if ok:
            report["screens"].append(path)

    # ---------- لقطة الصفحة كاملة ----------
    full = os.path.join(SHOTS, "desktop-full.png")
    result = cli_fullpage_capture(full, 1440)
    ok = result is not None
    check("لقطة الصفحة كاملة", ok,
          "%.0f KB" % (os.path.getsize(full) / 1024.0) if ok else "فشل")
    if ok:
        report["screens"].append(full)

    # ---------- ملف PDF للطباعة ----------
    pdf_path = os.path.join(SHOTS, "ha-cv.pdf")
    result = cli_capture(pdf_path, 1440, 900, pdf=True)
    check("توليد ملف PDF للطباعة", result is not None,
          "%.0f KB" % (os.path.getsize(pdf_path) / 1024.0) if result else "فشل")
    if result:
        report["screens"].append(pdf_path)

    # ---------- لقطة النسخة الإنجليزية ----------
    en_path = os.path.join(SHOTS, "desktop-english.png")
    result = cli_capture(en_path, 1440, 900, url=URL + "?static=1&lang=en")
    check("لقطة النسخة الإنجليزية", result is not None,
          "%.0f KB" % (os.path.getsize(en_path) / 1024.0) if result else "فشل")
    if result:
        report["screens"].append(en_path)

    # ---------- أحجام الشاشات ----------
    print("\n-- أحجام الشاشات --")
    port = 9344
    proc = run_chrome(port, 1440, 900)
    session = Session(port)
    try:
        session.connect()
        session.command("Page.enable")
        session.command("Runtime.enable")
        session.command("Network.enable")

        for name, width, height in VIEWPORTS:
            session.command("Emulation.setDeviceMetricsOverride", {
                "width": width, "height": height, "deviceScaleFactor": 1,
                "mobile": width < 800})
            session.command("Page.navigate", {"url": URL})
            time.sleep(3.2)

            over = session.evaluate("""(function(){
                var d=document.documentElement;
                var bad=[];
                Array.prototype.forEach.call(document.querySelectorAll('body *'), function(el){
                    var r=el.getBoundingClientRect();
                    if (r.width>0 && (r.right > window.innerWidth+2 || r.left < -2)) {
                        var cs=getComputedStyle(el);
                        if (cs.position!=='fixed' && el.offsetParent!==null) {
                            bad.push(el.tagName+'.'+(el.className||'').toString().split(' ')[0]);
                        }
                    }
                });
                return {over: d.scrollWidth - window.innerWidth,
                        offenders: Array.from(new Set(bad)).slice(0,6)};
            })()""")
            check("لا تمرير أفقي @%dx%d" % (width, height), over["over"] <= 1,
                  "فرق=%dpx %s" % (over["over"], over["offenders"]))

            session.evaluate("window.scrollTo(0,0)")
            time.sleep(0.8)

            # اختبار قائمة الجوال
            if width < 900:
                session.evaluate("document.getElementById('navToggle').click()")
                time.sleep(0.9)
                menu = session.evaluate("""(function(){
                    var n=document.getElementById('primaryNav');
                    var r=n.getBoundingClientRect();
                    return {open:n.classList.contains('is-open'),
                            visible:r.right<=window.innerWidth+2 && r.left>=-2,
                            expanded:document.getElementById('navToggle').getAttribute('aria-expanded')};
                })()""")
                check("قائمة الجوال تفتح صح @%dpx" % width,
                      menu["open"] and menu["visible"] and menu["expanded"] == "true",
                      json.dumps(menu, ensure_ascii=False))
                session.evaluate("document.getElementById('navToggle').click()")
                time.sleep(0.5)

    finally:
        try:
            proc.terminate()
        except Exception:
            pass

    # ---------- التقرير ----------
    passed = sum(1 for c in report["checks"] if c["ok"])
    total = len(report["checks"])
    print("\n" + "=" * 74)
    print("  النتيجة: %d / %d فحص ناجح" % (passed, total))
    print("=" * 74)
    failed = [c for c in report["checks"] if not c["ok"]]
    if failed:
        print("\nفحوصات فاشلة:")
        for c in failed:
            print("  - %s  (%s)" % (c["name"], c["detail"]))
    if report["errors"]:
        print("\nأخطاء JS:")
        for e in report["errors"]:
            print("  - %s" % e)

    with open(os.path.join(SHOTS, "report.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print("\nتم حفظ التقرير في tools/shots/report.json\n")
    return 0 if passed == total and not report["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
