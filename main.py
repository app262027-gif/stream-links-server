from kivy.config import Config

# ---------- إعدادات النافذة (لازم تكون قبل أي import ثاني من kivy) ----------
Config.set("graphics", "width", "640")       # عرض النافذة (مربعة)
Config.set("graphics", "height", "640")      # طول النافذة (مربعة)
Config.set("graphics", "resizable", "0")     # بيلغي زر التكبير (المربع) وبيمنع تغيير الحجم

import math
import secrets
import string
import threading
from datetime import datetime, timedelta, timezone

import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle, Triangle
from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

# ---------- الألوان ----------
BG_COLOR = (0.043, 0.055, 0.075, 1)
CARD_COLOR = (0.157, 0.188, 0.255, 1)
CARD_BORDER = (0.200, 0.235, 0.310, 1)
INPUT_COLOR = (0.118, 0.133, 0.200, 1)
INPUT_BORDER = (0.200, 0.235, 0.310, 1)
BTN_COLOR = (0.110, 0.125, 0.188, 1)
BTN_BORDER = (0.200, 0.235, 0.310, 1)
BTN_PRESSED = (0.150, 0.170, 0.245, 1)
LABEL_COLOR = (0.663, 0.706, 0.784, 1)
TEXT_COLOR = (0.93, 0.95, 0.98, 1)
BTN_TEXT_COLOR = (0.545, 0.592, 0.680, 1)
ACCENT_LEFT = (0.90, 0.93, 0.97, 1)

Window.clearcolor = BG_COLOR
Window.softinput_mode = "below_target"

# ---------- رابط الـ API ----------
API_URL = "https://stream-links-server.onrender.com/generate/"

# ---------- مدة الاشتراك ----------
TRIAL_DURATION_HOURS = 24

# (المفتاح، النص على الزر، عدد الأيام)
DURATIONS = [
    ("1m", "1 mo", 30),
    ("3m", "3 mo", 90),
    ("6m", "6 mo", 180),
    ("1y", "1 yr", 365),
    ("2y", "2 yr", 730),
]
DEFAULT_DURATION = "1y"
DURATION_DAYS = {key: days for key, _, days in DURATIONS}


def build_expiry(mode, duration_key=None):
    """يرجع dict فيه مدة الاشتراك وتاريخ الانتهاء (UTC) حسب الوضع."""
    now = datetime.now(timezone.utc)
    if mode == "trial":
        return {
            "duration_hours": TRIAL_DURATION_HOURS,
            "expires_at": (now + timedelta(hours=TRIAL_DURATION_HOURS)).isoformat(),
        }
    days = DURATION_DAYS.get(duration_key, DURATION_DAYS[DEFAULT_DURATION])
    return {
        "duration_days": days,
        "expires_at": (now + timedelta(days=days)).isoformat(),
    }


def send_to_api(username, password, mode, duration_key=None):
    def _send():
        try:
            payload = {
                "username": username,
                "password": password,
                "mode": mode,
            }
            payload.update(build_expiry(mode, duration_key))

            response = requests.post(
                API_URL,
                json=payload,
                headers={"x-api-key": "my-secret-key-123"},
                timeout=5,
            )
            print("API Response:", response.json())
        except Exception as e:
            print("API Error:", e)
    threading.Thread(target=_send, daemon=True).start()


# ---------- دوال التوليد ----------
def random_number(length=10):
    first = str(secrets.randbelow(9) + 1)
    rest = "".join(str(secrets.randbelow(10)) for _ in range(length - 1))
    return first + rest


LETTERS_DIGITS = string.ascii_letters + string.digits
NAMES = [
    "ahmad", "mohammad", "omar", "khaled", "yousef", "ali", "hassan", "hussein",
    "ibrahim", "mahmoud", "samer", "fadi", "rami", "tarek", "bilal", "nour",
    "layla", "sara", "maya", "lina", "rana", "hiba", "dana", "rima",
]


def random_alnum(length=10):
    while True:
        value = "".join(secrets.choice(LETTERS_DIGITS) for _ in range(length))
        if any(c.isalpha() for c in value) and any(c.isdigit() for c in value):
            return value


def random_name():
    return secrets.choice(NAMES)


# ---------- أيقونة التحديث ----------
class RefreshIcon(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(24), dp(24))
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    def _arrow(self, cx, cy, r, ang, size):
        a = math.radians(ang)
        px, py = cx + r * math.sin(a), cy + r * math.cos(a)
        ux, uy = math.sin(a), math.cos(a)
        tx, ty = math.cos(a), -math.sin(a)
        tip = (px + tx * size * 1.1, py + ty * size * 1.1)
        b1 = (px - tx * size * 0.2 + ux * size, py - ty * size * 0.2 + uy * size)
        b2 = (px - tx * size * 0.2 - ux * size, py - ty * size * 0.2 - uy * size)
        return [tip[0], tip[1], b1[0], b1[1], b2[0], b2[1]]

    def _draw(self, *args):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        r = min(self.width, self.height) * 0.30
        lw = dp(1.8)
        with self.canvas:
            Color(*BTN_TEXT_COLOR)
            Line(circle=(cx, cy, r, 25, 145), width=lw)
            Line(circle=(cx, cy, r, 205, 325), width=lw)
            Triangle(points=self._arrow(cx, cy, r, 145, dp(4.5)))
            Triangle(points=self._arrow(cx, cy, r, 325, dp(4.5)))


# ---------- خانة الإدخال ----------
class RoundedInput(BoxLayout):
    def __init__(self, text="", hint_text="", **kwargs):
        super().__init__(
            size_hint_y=None,
            height=dp(52),
            padding=dp(1),
            **kwargs,
        )
        with self.canvas.before:
            Color(*INPUT_BORDER)
            self._r_border = RoundedRectangle(radius=[dp(8)])
            Color(*INPUT_COLOR)
            self._r_fill = RoundedRectangle(radius=[dp(8)])
        self.bind(pos=self._update, size=self._update)

        self.ti = TextInput(
            text=text,
            hint_text=hint_text,
            multiline=False,
            write_tab=False,
            background_normal="",
            background_active="",
            background_disabled_normal="",
            background_color=(0, 0, 0, 0),
            foreground_color=TEXT_COLOR,
            hint_text_color=(0.45, 0.50, 0.60, 1),
            cursor_color=TEXT_COLOR,
            selection_color=(0.35, 0.45, 0.70, 0.45),
            font_size=sp(19),
            padding=[dp(16), dp(13), dp(16), dp(10)],
        )
        self.add_widget(self.ti)
        self._update()

    @property
    def text(self):
        return self.ti.text

    @text.setter
    def text(self, value):
        self.ti.text = value

    @property
    def hint_text(self):
        return self.ti.hint_text

    @hint_text.setter
    def hint_text(self, value):
        self.ti.hint_text = value

    def _update(self, *args):
        self._r_border.pos = self.pos
        self._r_border.size = self.size
        self._r_fill.pos = (self.x + dp(1), self.y + dp(1))
        self._r_fill.size = (self.width - dp(2), self.height - dp(2))


# ---------- زر Generate Random ----------
class GenerateButton(ButtonBehavior, BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(12),
            padding=[dp(8), 0, dp(8), 0],
            **kwargs,
        )
        with self.canvas.before:
            self._c_border = Color(*BTN_BORDER)
            self._r_border = RoundedRectangle(radius=[dp(8)])
            self._c_fill = Color(*BTN_COLOR)
            self._r_fill = RoundedRectangle(radius=[dp(8)])
            self._c_accent = Color(*ACCENT_LEFT)
            self._accent = RoundedRectangle(radius=[dp(8), 0, 0, dp(8)])

        self.add_widget(Widget())
        self.icon = RefreshIcon()
        self.icon.pos_hint = {"center_y": 0.5}
        self.add_widget(self.icon)
        self.label = Label(
            text="Generate Random",
            font_size=sp(18),
            color=BTN_TEXT_COLOR,
            size_hint=(None, 1),
        )
        self.label.bind(texture_size=lambda w, ts: setattr(w, "width", ts[0]))
        self.add_widget(self.label)
        self.add_widget(Widget())

        self.bind(pos=self._update, size=self._update, state=self._on_state)
        self._update()

    def _on_state(self, *args):
        self._c_fill.rgba = BTN_PRESSED if self.state == "down" else BTN_COLOR

    def _update(self, *args):
        self._r_border.pos = self.pos
        self._r_border.size = self.size
        self._r_fill.pos = (self.x + dp(1), self.y + dp(1))
        self._r_fill.size = (self.width - dp(2), self.height - dp(2))
        self._accent.pos = self.pos
        self._accent.size = (dp(2), self.height)


# ---------- قسم كامل (عنوان + خانة + زر) ----------
class Section(BoxLayout):
    def __init__(self, title, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10),
            **kwargs,
        )
        self.generator = random_number
        self.card_ref = None  # مرجع للكارد عشان نعرف الـ mode
        self.height = dp(34) + dp(52) + dp(52) + dp(20)

        self.title = Label(
            text=title,
            font_size=sp(19),
            color=LABEL_COLOR,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(34),
        )
        self.title.bind(size=lambda w, s: setattr(w, "text_size", s))
        self.input = RoundedInput(text="")
        self.button = GenerateButton()
        self.button.bind(on_release=self.generate)

        self.add_widget(self.title)
        self.add_widget(self.input)
        self.add_widget(self.button)

    def generate(self, *args):
        value = self.generator()
        self.input.text = value
        print("generated:", value)

        # إرسال للـ API إذا كان عندنا مرجع للكارد
        if self.card_ref:
            username = self.card_ref.username.input.text
            password = self.card_ref.password.input.text
            mode = getattr(self.card_ref, "mode", "trial")
            duration_key = getattr(self.card_ref, "duration", DEFAULT_DURATION)
            # إرسال فقط إذا الاثنين موجودين
            if username and password:
                send_to_api(username, password, mode, duration_key)

    def configure(self, generator, hint="", autofill=True):
        self.generator = generator
        self.input.hint_text = hint
        self.input.text = generator() if autofill else ""


# ---------- أزرار اختيار نوع الاشتراك ----------
class ModeButton(ButtonBehavior, Label):
    def __init__(self, text, font_size=None, **kwargs):
        super().__init__(text=text, font_size=font_size or sp(17), **kwargs)
        self.active = False
        with self.canvas.before:
            self._c = Color(*BTN_COLOR)
            self._r = RoundedRectangle(radius=[dp(8)])
        self.bind(pos=self._update, size=self._update)
        self.set_active(False)

    def set_active(self, active):
        self.active = active
        self._c.rgba = (0.24, 0.31, 0.48, 1) if active else BTN_COLOR
        self.color = TEXT_COLOR if active else BTN_TEXT_COLOR

    def _update(self, *args):
        self._r.pos = self.pos
        self._r.size = self.size


# ---------- الكارد ----------
class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(0.92, None),
            padding=[dp(22), dp(22), dp(22), dp(26)],
            spacing=dp(28),
            **kwargs,
        )
        with self.canvas.before:
            Color(*CARD_BORDER)
            self._r_border = RoundedRectangle(radius=[dp(12)])
            Color(*CARD_COLOR)
            self._r_fill = RoundedRectangle(radius=[dp(12)])
        self.bind(pos=self._update, size=self._update)

        self.mode = "trial"
        self.duration = DEFAULT_DURATION

        modes = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        self.btn_trial = ModeButton("Trial")
        self.btn_annual = ModeButton("Annual")
        self.btn_trial.bind(on_release=lambda *a: self.set_mode("trial"))
        self.btn_annual.bind(on_release=lambda *a: self.set_mode("annual"))
        modes.add_widget(self.btn_trial)
        modes.add_widget(self.btn_annual)
        self.add_widget(modes)

        # صف خيارات المدة (بيظهر فقط بالوضع التاني)
        self.durations_bar = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        self.duration_buttons = {}
        for key, label, _days in DURATIONS:
            btn = ModeButton(label, font_size=sp(14))
            btn.bind(on_release=lambda w, k=key: self.set_duration(k))
            self.duration_buttons[key] = btn
            self.durations_bar.add_widget(btn)
        self._durations_visible = False

        self.username = Section("Username")
        self.password = Section("Password")

        # ربط الـ Section بالكارد
        self.username.card_ref = self
        self.password.card_ref = self

        self.add_widget(self.username)
        self.add_widget(self.password)

        # زر نسخ الكل (اليوزر + الباسورد بكبسة وحدة)
        self.btn_copy = ModeButton("Copy All")
        self.btn_copy.size_hint_y = None
        self.btn_copy.height = dp(46)
        self.btn_copy.set_active(True)
        self.btn_copy.bind(on_release=self.copy_all)
        self.add_widget(self.btn_copy)

        self.bind(minimum_height=self.setter("height"))
        Clock.schedule_once(lambda dt: self.set_mode("trial"), 0)

    def copy_all(self, *args):
        username = self.username.input.text
        password = self.password.input.text
        if not username and not password:
            return
        Clipboard.copy(f"Username: {username}\nPassword: {password}")
        self.btn_copy.text = "Copied!"
        Clock.schedule_once(lambda dt: setattr(self.btn_copy, "text", "Copy All"), 1.5)

    def _show_durations(self, show):
        if show and not self._durations_visible:
            # children مرتبة بالعكس: نحطه مباشرة تحت صف Trial/Annual
            self.add_widget(self.durations_bar, index=len(self.children) - 1)
            self._durations_visible = True
        elif not show and self._durations_visible:
            self.remove_widget(self.durations_bar)
            self._durations_visible = False

    def set_duration(self, key):
        self.duration = key
        for k, btn in self.duration_buttons.items():
            btn.set_active(k == key)

    def set_mode(self, mode):
        self.mode = mode
        self.btn_trial.set_active(mode == "trial")
        self.btn_annual.set_active(mode == "annual")
        if mode == "trial":
            self._show_durations(False)
            self.username.configure(random_number)
            self.password.configure(random_number)
        else:
            self._show_durations(True)
            self.set_duration(self.duration)
            self.username.configure(random_name, hint="Enter person's name", autofill=False)
            self.password.configure(random_alnum)

    def _update(self, *args):
        self._r_border.pos = self.pos
        self._r_border.size = self.size
        self._r_fill.pos = (self.x + dp(1), self.y + dp(1))
        self._r_fill.size = (self.width - dp(2), self.height - dp(2))


class RandomGeneratorApp(App):
    title = "Random Generator"

    def build(self):
        root = AnchorLayout(anchor_x="center", anchor_y="center")
        root.add_widget(Card())
        return root


if __name__ == "__main__":
    RandomGeneratorApp().run()