import os
import sys
import json
import secrets
import inspect
import asyncio
import threading
import webbrowser
import urllib.request

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.carousel import Carousel
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox

BG_COLOR = get_color_from_hex("#18191D")
CARD_COLOR = get_color_from_hex("#22242A")
BORDER_COLOR = get_color_from_hex("#32353E")
INPUT_COLOR = get_color_from_hex("#141519")
BLUE_ACCENT = get_color_from_hex("#2B86F6")
GREEN_BTN = get_color_from_hex("#23B25D")
RED_BTN = get_color_from_hex("#E03E3E")
TEXT_GRAY = get_color_from_hex("#9AA0A6")

Window.clearcolor = BG_COLOR

DEFAULT_CONFIG = {
    "ip": "127.0.0.1",
    "port": "1443",
    "secret": "723c0776b43af7043e7c03ce414c12c5",
    "dc_ips": (
        "4:162.159.130.54\n"
        "4:162.159.131.177\n"
        "4:141.101.122.174\n"
        "4:162.159.133.221\n"
        "4:141.101.114.189\n"
        "2:149.154.167.220\n"
        "5:91.108.56.100"
    ),
    "cf_proxy_enabled": True,
    "cf_http2": True,
    "cf_custom_enabled": False,
    "cf_custom_domain": "",
    "cf_worker_enabled": True,
    "cf_worker_domain": "late-snow-ee79.kononovmaks2008.workers.dev",
    "verbose": False,
    "disable_tls": True,
    "buffer_kb": "256",
    "ws_pool": "4",
    "max_log_mb": "5.0"
}


class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(14), spacing=dp(10), size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter("height"))
        with self.canvas.before:
            Color(*CARD_COLOR)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(*BORDER_COLOR)
            self.line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(10)), width=1)
        self.bind(pos=self._update_graphics, size=self._update_graphics)

    def _update_graphics(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(10))


def make_title(text):
    lbl = Label(
        text=f"[b]{text}[/b]",
        markup=True,
        font_size=dp(16),
        color=(1, 1, 1, 1),
        size_hint_y=None,
        height=dp(26),
        halign="left",
        valign="middle"
    )
    lbl.bind(size=lbl.setter("text_size"))
    return lbl


def make_sub_label(text):
    lbl = Label(
        text=text,
        font_size=dp(13),
        color=TEXT_GRAY,
        size_hint_y=None,
        height=dp(20),
        halign="left",
        valign="middle"
    )
    lbl.bind(size=lbl.setter("text_size"))
    return lbl


def make_input(text="", multiline=False, height_dp=42):
    return TextInput(
        text=text,
        multiline=multiline,
        size_hint_y=None,
        height=dp(height_dp),
        background_normal="",
        background_active="",
        background_color=INPUT_COLOR,
        foreground_color=(1, 1, 1, 1),
        cursor_color=BLUE_ACCENT,
        font_size=dp(14),
        padding=[dp(10), dp(10), dp(10), dp(10)]
    )


def make_checkbox_row(text, active=False, right_btn=None):
    row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(8))
    cb = CheckBox(active=active, size_hint_x=None, width=dp(32), color=BLUE_ACCENT)
    lbl = Label(text=text, font_size=dp(14), color=(1, 1, 1, 1), halign="left", valign="middle")
    lbl.bind(size=lbl.setter("text_size"))
    row.add_widget(cb)
    row.add_widget(lbl)
    if right_btn:
        row.add_widget(right_btn)
    return row, cb


class TGWSProxyMobileApp(App):
    def build(self):
        self.config_path = os.path.join(self.user_data_dir, "settings.json")
        self.cfg = self.load_cfg()
        self.proxy_running = False
        self.proxy_loop = None

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))

        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(42), spacing=dp(8))
        title_lbl = Label(
            text="[b]TG WS Proxy — Настройки[/b]",
            markup=True,
            font_size=dp(18),
            halign="left",
            valign="middle"
        )
        title_lbl.bind(size=title_lbl.setter("text_size"))
        ver_lbl = Label(text="v1.11.2", font_size=dp(13), color=TEXT_GRAY, size_hint_x=None, width=dp(55))
        header.add_widget(title_lbl)
        header.add_widget(ver_lbl)
        root.add_widget(header)

        self.tab_bar = GridLayout(cols=4, size_hint_y=None, height=dp(36), spacing=dp(6))
        self.tab_buttons = []
        for idx, name in enumerate(["1. Запуск", "2. MTProto", "3. CF Домен", "4. Сеть"]):
            btn = Button(
                text=name,
                font_size=dp(12),
                background_normal="",
                background_color=BLUE_ACCENT if idx == 0 else CARD_COLOR
            )
            btn.bind(on_press=lambda _, i=idx: self.switch_page(i))
            self.tab_buttons.append(btn)
            self.tab_bar.add_widget(btn)
        root.add_widget(self.tab_bar)

        root.add_widget(Label(
            text="Свайпай вправо/влево для переключения страниц",
            font_size=dp(11),
            color=TEXT_GRAY,
            size_hint_y=None,
            height=dp(18)
        ))

        self.carousel = Carousel(direction="right", loop=False)
        self.carousel.bind(index=self.on_carousel_swipe)
        self.carousel.add_widget(self.build_page_launch())
        self.carousel.add_widget(self.build_page_mtproto())
        self.carousel.add_widget(self.build_page_cloudflare())
        self.carousel.add_widget(self.build_page_logs_perf())
        root.add_widget(self.carousel)

        bottom = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(46), spacing=dp(10))
        btn_save = Button(text="Сохранить", font_size=dp(15), bold=True, background_normal="", background_color=BLUE_ACCENT)
        btn_save.bind(on_press=self.on_save_pressed)
        btn_reset = Button(text="Сброс", font_size=dp(14), size_hint_x=0.4, background_normal="", background_color=CARD_COLOR)
        btn_reset.bind(on_press=self.on_reset_pressed)
        bottom.add_widget(btn_save)
        bottom.add_widget(btn_reset)
        root.add_widget(bottom)
        return root

    def wrap_scroll(self, content_box):
        sv = ScrollView(do_scroll_x=False)
        sv.add_widget(content_box)
        return sv

    def build_page_launch(self):
        box = BoxLayout(orientation="vertical", spacing=dp(12), padding=[0, dp(6), 0, dp(6)], size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        box.add_widget(make_title("Управление прокси"))
        card = Card()
        self.status_lbl = Label(
            text="[b]Статус: ОСТАНОВЛЕН[/b]\nНажми кнопку ниже для запуска",
            markup=True, font_size=dp(15), halign="center", valign="middle", size_hint_y=None, height=dp(54)
        )
        self.status_lbl.bind(size=self.status_lbl.setter("text_size"))
        card.add_widget(self.status_lbl)

        self.btn_start = Button(
            text="ЗАПУСТИТЬ ПРОКСИ", font_size=dp(18), bold=True,
            size_hint_y=None, height=dp(58), background_normal="", background_color=GREEN_BTN
        )
        self.btn_start.bind(on_press=self.toggle_proxy)
        card.add_widget(self.btn_start)

        btn_tg = Button(
            text="Подключить в Telegram (MTProto)", font_size=dp(15),
            size_hint_y=None, height=dp(44), background_normal="", background_color=BLUE_ACCENT
        )
        btn_tg.bind(on_press=self.connect_telegram)
        card.add_widget(btn_tg)
        box.add_widget(card)

        box.add_widget(make_title("Журнал работы (Лог)"))
        log_card = Card()
        self.log_box = make_input("Готов к запуску.\n", multiline=True, height_dp=190)
        self.log_box.readonly = True
        log_card.add_widget(self.log_box)
        box.add_widget(log_card)
        return self.wrap_scroll(box)

    def build_page_mtproto(self):
        box = BoxLayout(orientation="vertical", spacing=dp(12), padding=[0, dp(6), 0, dp(6)], size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        box.add_widget(make_title("Подключение MTProto"))
        card_mt = Card()

        row_ip = BoxLayout(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(68))
        col_ip = BoxLayout(orientation="vertical", spacing=dp(4))
        col_ip.add_widget(make_sub_label("IP-адрес"))
        self.in_ip = make_input(self.cfg["ip"])
        col_ip.add_widget(self.in_ip)

        col_port = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_x=0.45)
        col_port.add_widget(make_sub_label("Порт"))
        self.in_port = make_input(self.cfg["port"])
        col_port.add_widget(self.in_port)

        row_ip.add_widget(col_ip)
        row_ip.add_widget(col_port)
        card_mt.add_widget(row_ip)

        card_mt.add_widget(make_sub_label("Ключ"))
        row_sec = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(42))
        self.in_secret = make_input(self.cfg["secret"])
        btn_gen = Button(text="↻", font_size=dp(20), size_hint_x=None, width=dp(44), background_normal="", background_color=BLUE_ACCENT)
        btn_gen.bind(on_press=lambda _: setattr(self.in_secret, "text", secrets.token_hex(16)))
        row_sec.add_widget(self.in_secret)
        row_sec.add_widget(btn_gen)
        card_mt.add_widget(row_sec)
        box.add_widget(card_mt)

        box.add_widget(make_title("Датацентры Telegram (DC → IP)"))
        card_dc = Card()
        card_dc.add_widget(make_sub_label("По одному правилу на строку, формат: номер:IP"))
        self.in_dc = make_input(self.cfg["dc_ips"], multiline=True, height_dp=150)
        card_dc.add_widget(self.in_dc)
        box.add_widget(card_dc)
        return self.wrap_scroll(box)

    def build_page_cloudflare(self):
        box = BoxLayout(orientation="vertical", spacing=dp(12), padding=[0, dp(6), 0, dp(6)], size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        box.add_widget(make_title("Cloudflare Proxy"))
        card_cf = Card()

        btn_test_cf = Button(text="Тест", size_hint=(None, None), size=(dp(68), dp(32)), background_normal="", background_color=BLUE_ACCENT)
        btn_test_cf.bind(on_press=lambda _: self.test_domain(self.in_cf_domain.text or "162.159.130.54"))

        row_cf_en, self.cb_cf_en = make_checkbox_row("Включить CF-прокси", self.cfg["cf_proxy_enabled"], btn_test_cf)
        row_cf_h2, self.cb_cf_h2 = make_checkbox_row("Мультиплексирование медиа (HTTP/2)", self.cfg["cf_http2"])
        row_cf_cust, self.cb_cf_cust = make_checkbox_row("Свой домен", self.cfg["cf_custom_enabled"])
        self.in_cf_domain = make_input(self.cfg["cf_custom_domain"])

        card_cf.add_widget(row_cf_en)
        card_cf.add_widget(row_cf_h2)
        card_cf.add_widget(row_cf_cust)
        card_cf.add_widget(self.in_cf_domain)
        box.add_widget(card_cf)

        box.add_widget(make_title("Cloudflare Worker"))
        card_wk = Card()
        top_wk = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32))
        top_wk.add_widget(make_sub_label("Cloudflare Worker домены (через запятую)"))
        btn_test_wk = Button(text="Тест", size_hint=(None, None), size=(dp(68), dp(32)), background_normal="", background_color=BLUE_ACCENT)
        btn_test_wk.bind(on_press=lambda _: self.test_domain(self.in_wk_domain.text))
        top_wk.add_widget(btn_test_wk)
        card_wk.add_widget(top_wk)

        row_wk_en, self.cb_wk_en = make_checkbox_row("Свой домен", self.cfg["cf_worker_enabled"])
        card_wk.add_widget(row_wk_en)
        self.in_wk_domain = make_input(self.cfg["cf_worker_domain"])
        card_wk.add_widget(self.in_wk_domain)
        box.add_widget(card_wk)
        return self.wrap_scroll(box)

    def build_page_logs_perf(self):
        box = BoxLayout(orientation="vertical", spacing=dp(12), padding=[0, dp(6), 0, dp(6)], size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        box.add_widget(make_title("Логи и производительность"))
        card_lp = Card()

        row_verb, self.cb_verbose = make_checkbox_row("Подробное логирование (verbose)", self.cfg["verbose"])
        row_tls, self.cb_no_tls = make_checkbox_row("Выключить TLS для CF-прокси и CF-worker", self.cfg["disable_tls"])
        card_lp.add_widget(row_verb)
        card_lp.add_widget(row_tls)

        card_lp.add_widget(make_sub_label("Буфер, КБ (по умолчанию 256)"))
        self.in_buf = make_input(self.cfg["buffer_kb"])
        card_lp.add_widget(self.in_buf)

        card_lp.add_widget(make_sub_label("Пул WebSocket-сессий (по умолчанию 4)"))
        self.in_pool = make_input(self.cfg["ws_pool"])
        card_lp.add_widget(self.in_pool)

        card_lp.add_widget(make_sub_label("Макс. размер лога, МБ (по умолчанию 5)"))
        self.in_log_mb = make_input(self.cfg["max_log_mb"])
        card_lp.add_widget(self.in_log_mb)

        box.add_widget(card_lp)
        return self.wrap_scroll(box)

    def switch_page(self, idx):
        self.carousel.load_slide(self.carousel.slides[idx])

    def on_carousel_swipe(self, instance, value):
        for i, btn in enumerate(self.tab_buttons):
            btn.background_color = BLUE_ACCENT if i == value else CARD_COLOR

    def log(self, msg):
        Clock.schedule_once(lambda dt: setattr(self.log_box, "text", self.log_box.text + f"{msg}\n"), 0)

    def collect_ui_config(self):
        return {
            "ip": self.in_ip.text.strip() or "127.0.0.1",
            "port": self.in_port.text.strip() or "1443",
            "secret": self.in_secret.text.strip(),
            "dc_ips": self.in_dc.text.strip(),
            "cf_proxy_enabled": self.cb_cf_en.active,
            "cf_http2": self.cb_cf_h2.active,
            "cf_custom_enabled": self.cb_cf_cust.active,
            "cf_custom_domain": self.in_cf_domain.text.strip(),
            "cf_worker_enabled": self.cb_wk_en.active,
            "cf_worker_domain": self.in_wk_domain.text.strip(),
            "verbose": self.cb_verbose.active,
            "disable_tls": self.cb_no_tls.active,
            "buffer_kb": self.in_buf.text.strip() or "256",
            "ws_pool": self.in_pool.text.strip() or "4",
            "max_log_mb": self.in_log_mb.text.strip() or "5.0"
        }

    def load_cfg(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    merged = DEFAULT_CONFIG.copy()
                    merged.update(json.load(f))
                    return merged
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def on_save_pressed(self, _):
        self.cfg = self.collect_ui_config()
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f, ensure_ascii=False, indent=2)
            self.log("[✓] Настройки сохранены!")
        except Exception as e:
            self.log(f"[!] Ошибка: {e}")

    def on_reset_pressed(self, _):
        self.cfg = DEFAULT_CONFIG.copy()
        self.in_ip.text = self.cfg["ip"]
        self.in_port.text = self.cfg["port"]
        self.in_secret.text = self.cfg["secret"]
        self.in_dc.text = self.cfg["dc_ips"]
        self.cb_cf_en.active = self.cfg["cf_proxy_enabled"]
        self.cb_cf_h2.active = self.cfg["cf_http2"]
        self.cb_cf_cust.active = self.cfg["cf_custom_enabled"]
        self.in_cf_domain.text = self.cfg["cf_custom_domain"]
        self.cb_wk_en.active = self.cfg["cf_worker_enabled"]
        self.in_wk_domain.text = self.cfg["cf_worker_domain"]
        self.cb_verbose.active = self.cfg["verbose"]
        self.cb_no_tls.active = self.cfg["disable_tls"]
        self.in_buf.text = self.cfg["buffer_kb"]
        self.in_pool.text = self.cfg["ws_pool"]
        self.in_log_mb.text = self.cfg["max_log_mb"]
        self.log("[i] Настройки сброшены.")

    def test_domain(self, domain_str):
        domain = domain_str.split(",")[0].strip().replace("https://", "").replace("http://", "").strip("/")
        if not domain:
            return
        self.log(f"[Тест] Проверка {domain}...")

        def _check():
            try:
                scheme = "http" if self.cb_no_tls.active else "https"
                req = urllib.request.Request(f"{scheme}://{domain}", headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    self.log(f"[Тест ОК] {domain} (код {resp.status})")
            except Exception as e:
                self.log(f"[Тест] Ответ {domain}: {e}")

        threading.Thread(target=_check, daemon=True).start()
        self.switch_page(0)

    def connect_telegram(self, _):
        cfg = self.collect_ui_config()
        secret = cfg["secret"]
        if not secret.startswith("dd") and len(secret) == 32:
            secret = "dd" + secret
        webbrowser.open(f"tg://proxy?server={cfg['ip']}&port={cfg['port']}&secret={secret}")

    def toggle_proxy(self, _):
        if not self.proxy_running:
            self.on_save_pressed(None)
            self.proxy_running = True
            self.btn_start.text = "ОСТАНОВИТЬ ПРОКСИ"
            self.btn_start.background_color = RED_BTN
            self.status_lbl.text = f"[b]Статус: АКТИВЕН ({self.cfg['ip']}:{self.cfg['port']})[/b]"
            threading.Thread(target=self.run_flowseal_thread, daemon=True).start()
        else:
            self.proxy_running = False
            if self.proxy_loop:
                self.proxy_loop.call_soon_threadsafe(self.proxy_loop.stop)
            self.btn_start.text = "ЗАПУСТИТЬ ПРОКСИ"
            self.btn_start.background_color = GREEN_BTN
            self.status_lbl.text = "[b]Статус: ОСТАНОВЛЕН[/b]"
            self.log("[*] Прокси остановлен.")

    def build_cli_args(self, supported_flags):
        c = self.cfg
        args = ["tg_ws_proxy.py"]

        def add_opt(flag_variants, val=None):
            for fl in flag_variants:
                if not supported_flags or fl in supported_flags:
                    args.append(fl)
                    if val is not None:
                        args.append(str(val))
                    return

        add_opt(["--host", "-H"], c["ip"])
        add_opt(["--port", "-p"], c["port"])
        if c["secret"]:
            add_opt(["--secret", "-s"], c["secret"])
        for line in c["dc_ips"].splitlines():
            if ":" in line.strip():
                add_opt(["--dc-ip"], line.strip())
        if c["cf_proxy_enabled"]:
            add_opt(["--cf-proxy", "--enable-cf-proxy"])
        if c["cf_http2"]:
            add_opt(["--cf-http2", "--http2"])
        if c["cf_custom_enabled"] and c["cf_custom_domain"]:
            add_opt(["--cf-domain", "--cfproxy-domain"], c["cf_custom_domain"])
        if c["cf_worker_enabled"] and c["cf_worker_domain"]:
            add_opt(["--cf-worker-domain", "--cfproxy-worker-domain", "--worker-domain"], c["cf_worker_domain"])
        if c["verbose"]:
            add_opt(["--verbose", "-v"])
        if c["disable_tls"]:
            add_opt(["--no-tls", "--disable-tls", "--cf-no-tls"])
        return args

    def run_flowseal_thread(self):
        try:
            base_dir = getattr(sys, "_MEIPASS", os.path.abspath("."))
            sys.path.insert(0, os.path.join(base_dir, "flowseal_core"))
            sys.path.insert(0, os.path.join(base_dir, "flowseal_core", "proxy"))
            import proxy.tg_ws_proxy as flowseal_mod
            import re
            supported = set(re.findall(r"['\"](--[a-zA-Z0-9_-]+|-[a-zA-Z])['\"]", inspect.getsource(flowseal_mod)))
            sys.argv = self.build_cli_args(supported)
            self.log(f"[*] Старт: {' '.join(sys.argv[1:])}")

            self.proxy_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.proxy_loop)
            if hasattr(flowseal_mod, "amain"):
                self.proxy_loop.run_until_complete(flowseal_mod.amain())
            elif hasattr(flowseal_mod, "main"):
                res = flowseal_mod.main()
                if asyncio.iscoroutine(res):
                    self.proxy_loop.run_until_complete(res)
        except Exception as e:
            self.log(f"[!] Движок: {e}")


if __name__ == "__main__":
    TGWSProxyMobileApp().run()
