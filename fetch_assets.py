# -*- coding: utf-8 -*-
"""
HA-Digital-Portfolio / tools/fetch_assets.py
------------------------------------------------------------------
أداة تحميل ومعالجة الصور محليًا لمشروع HA-Digital-Portfolio.

الوظيفة:
  1. تحميل صور عالية الجودة من مصدر مفتوح (Unsplash CDN).
  2. قصّ الصور وتحويلها إلى الأبعاد المطلوبة مع الحفاظ على نسبة الأبعاد.
  3. تطبيق معالجة لونية موحّدة (Duotone) تماشيًا مع هوية الموقع:
     Deep Burgundy #3E1C27  +  Champagne Gold #C5A46D.
  4. توليد صورة شخصية بديلة (Placeholder) بصيغة Monogram بدل استخدام
     صورة وجه حقيقية لا تملكها صاحبة السيرة.
  5. توليد أنماط هندسية (Patterns) و Favicon.

التشغيل:  python tools/fetch_assets.py
"""

import io
import os
import sys
import urllib.request
import urllib.error

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps

# ----------------------------------------------------------------------------
# المسارات
# ----------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "images")
PROJECTS = os.path.join(IMG, "projects")
BACKGROUNDS = os.path.join(IMG, "backgrounds")
os.makedirs(PROJECTS, exist_ok=True)
os.makedirs(BACKGROUNDS, exist_ok=True)

# ----------------------------------------------------------------------------
# لوحة ألوان الهوية البصرية — Lavender & Silver Luxury Technology
# ----------------------------------------------------------------------------
LAVENDER   = (0xC9, 0xB8, 0xF0)   # Lavender
PURPLE     = (0x54, 0x2B, 0x78)   # Deep Purple
LILAC      = (0xED, 0xE6, 0xFA)   # Soft Lilac
SILVER     = (0xC8, 0xCD, 0xD6)   # Silver
PEARL      = (0xFA, 0xF9, 0xFD)   # Pearl White
BLUE_LIGHT = (0xDC, 0xE7, 0xF5)   # Light Blue

# --- هوية Rose Quartz & Champagne ---
CREAM_PEARL = (0xFD, 0xF8, 0xF4)  # Cream Pearl
BLUSH_MIST  = (0xF8, 0xE9, 0xEA)  # Blush Mist
METALLIC    = (0xD3, 0xC6, 0xBC)  # Metallic Silver
CHAMPAGNE   = (0xE2, 0xC0, 0x8D)  # Champagne Gold
ROSE        = (0xE9, 0xA7, 0xB0)  # Soft Rose
BERRY       = (0x5A, 0x27, 0x40)  # Deep Berry
PLUM        = (0x8E, 0x55, 0x78)  # Mauve Plum

USER_AGENT = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HA-Portfolio/1.0"}


# ----------------------------------------------------------------------------
# أدوات مساعدة
# ----------------------------------------------------------------------------
def download(url: str, timeout: int = 30) -> bytes:
    """تحميل محتوى رابط مع ترويسة User-Agent لتفادي الحجب."""
    request = urllib.request.Request(url, headers=USER_AGENT)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def candidate_ids(ids):
    """يولّد روابط Unsplash بأحجام مختلفة لكل معرّف صورة."""
    for photo_id in ids:
        for width in (1600, 1200, 900):
            yield "https://images.unsplash.com/photo-%s?auto=format&fit=crop&w=%d&q=82" % (photo_id, width)
        yield "https://images.unsplash.com/photo-%s?auto=format&fit=crop&q=80" % photo_id


def fetch_image(ids, timeout=30):
    """يحاول تحميل أول رابط صالح من قائمة المعرّفات."""
    last_error = None
    for url in candidate_ids(ids):
        try:
            raw = download(url, timeout=timeout)
            image = Image.open(io.BytesIO(raw))
            image.load()
            return image
        except Exception as error:  # noqa: BLE001
            last_error = error
            continue
    raise RuntimeError("تعذّر تحميل الصورة: %s (%s)" % (ids, last_error))


def cover_resize(image: Image.Image, width: int, height: int) -> Image.Image:
    """قصّ الصورة لتغطية مساحة العرض المطلوبة ثم تصغيرها."""
    image = ImageOps.exif_transpose(image).convert("RGB")
    resized = ImageOps.fit(image, (width, height), method=Image.LANCZOS, centering=(0.5, 0.42))
    return resized


def duotone(image: Image.Image, dark=(0x2E, 0x14, 0x45), light=(0xDC, 0xE7, 0xF5), mix: float = 0.62):
    """
    يحوّل الصورة إلى تدرّج ثنائي اللون (Duotone) مع الحفاظ على تفاصيل الإضاءة،
    ثم يمزجه مع الأصل بنسبة mix للحصول على مظهر سينمائي ناعم.
    """
    grayscale = ImageOps.grayscale(image)
    grayscale = ImageOps.autocontrast(grayscale, cutoff=1)
    tinted = ImageOps.colorize(grayscale, black=dark, white=light)

    # تباين خفيف لرفع العمق اللوني
    tinted = ImageEnhance.Contrast(tinted).enhance(1.08)
    tinted = ImageEnhance.Color(tinted).enhance(1.05)
    return Image.blend(image, tinted, mix)


def warm_finish(image: Image.Image, strength: float = 0.16) -> Image.Image:
    """تدرّج لوني بارد خفيف يوحّد جميع الصور بصريًا."""
    overlay = Image.new("RGB", image.size, (0xC9, 0xB8, 0xF0))
    return Image.blend(image, overlay, strength)


def save_jpeg(image: Image.Image, path: str, quality=86, optimize=True):
    """حفظ كـ JPEG مع تحسين الحجم وضبط بيانات EXIF."""
    image.convert("RGB").save(path, "JPEG", quality=quality, optimize=optimize, progressive=True)
    size_kb = os.path.getsize(path) / 1024.0
    print("  [OK] %-58s %6.1f KB" % (os.path.relpath(path, ROOT), size_kb))


def save_png(image: Image.Image, path: str):
    """حفظ كـ PNG."""
    image.save(path, "PNG", optimize=True)
    size_kb = os.path.getsize(path) / 1024.0
    print("  [OK] %-58s %6.1f KB" % (os.path.relpath(path, ROOT), size_kb))


# ----------------------------------------------------------------------------
# 1) صور المشاريع
# ----------------------------------------------------------------------------
PROJECT_JOBS = [
    {
        "name": "project-building-materials.jpg",
        "ids": ["1541888946425-d81bb19240f5", "1503387762-592deb58ef4e",
                "1487958449943-2429e8be8625", "1590274853856-f22d5ee3d228"],
        "size": (1200, 800),
        "mix": 0.55,
        "grade": "construction",
    },
    {
        "name": "project-luxury-hospitality.jpg",
        "ids": ["1566073771259-6a8506099945", "1611892440504-42a792e24d32",
                "1571003123894-1f0594d2b5d9", "1445019980597-93fa8acb246c"],
        "size": (1200, 800),
        "mix": 0.62,
        "grade": "luxury",
    },
    {
        "name": "project-java-oop.jpg",
        "ids": ["1461749280684-dccba630e2f6", "1516116216624-53e697fedbea",
                "1555066931-4365d14bab8c", "1542831371-adb38447a05e"],
        "size": (1200, 800),
        "mix": 0.68,
        "grade": "code",
    },
    {
        "name": "project-hotel-database.jpg",
        "ids": ["1544383835-bda2bc66a55d", "1526374965328-7f61d4dc18c5",
                "1451187580459-43490279c0fa", "1558494949-ef010cbdcc31"],
        "size": (1200, 800),
        "mix": 0.66,
        "grade": "data",
    },
    {
        "name": "project-ai-research.jpg",
        "ids": ["1620712943543-bcc4688e7485", "1677442136019-21780ecad995",
                "1531746790731-6c087fecd65a", "1518770660439-4636190af475"],
        "size": (1200, 800),
        "mix": 0.70,
        "grade": "ai",
    },
]


def build_projects():
    print("\n== صور المشاريع ==")
    for job in PROJECT_JOBS:
        try:
            image = fetch_image(job["ids"])
        except RuntimeError as error:
            print("  [!!] %s -> %s" % (job["name"], error))
            continue
        image = cover_resize(image, job["size"][0], job["size"][1])
        # معالجة لونية لافندر/فضي متناسقة مع الهوية الجديدة
        image = duotone(image, dark=(0x2E, 0x14, 0x45), light=BLUE_LIGHT, mix=job["mix"])
        image = warm_finish(image, 0.08)
        image = ImageEnhance.Color(image).enhance(1.12)
        image = ImageEnhance.Sharpness(image).enhance(1.12)
        save_jpeg(image, os.path.join(PROJECTS, job["name"]), quality=84)


# ----------------------------------------------------------------------------
# 2) الخلفيات
# ----------------------------------------------------------------------------
BACKGROUND_JOBS = [
    {
        "name": "hero-tech.jpg",
        "ids": ["1451187580459-43490279c0fa", "1550751827-4bd374c3f58b",
                "1639762981054-0dd1d6f9e3a4", "1518770660439-4636190af475"],
        "size": (1920, 1080),
        "mix": 0.82,
        "blur": 0,
    },
    {
        "name": "vision-future.jpg",
        "ids": ["1451187580459-43490279c0fa", "1446776811953-b23d57bd21aa",
                "1519608487953-e999c86e7455", "1502920917128-1aa500764cbd"],
        "size": (1920, 1000),
        "mix": 0.88,
        "blur": 0,
    },
    {
        "name": "about-texture.jpg",
        "ids": ["1455390582262-044cdead277a", "1455885666463-54fe058a6e4a",
                "1481627834876-b7833e8f5570", "1519682337058-a94d519337bc"],
        "size": (1400, 1400),
        "mix": 0.90,
        "blur": 1.6,
    },
]


def build_backgrounds():
    print("\n== الخلفيات ==")
    for job in BACKGROUND_JOBS:
        try:
            image = fetch_image(job["ids"])
        except RuntimeError as error:
            print("  [!!] %s -> %s" % (job["name"], error))
            continue
        image = cover_resize(image, job["size"][0], job["size"][1])
        image = duotone(image, dark=(0x1C, 0x0C, 0x2C), light=(0x9E, 0x7E, 0xCE), mix=job["mix"])
        if job["blur"]:
            image = image.filter(ImageFilter.GaussianBlur(job["blur"]))
        # تعتيم متدرّج من الأسفل للأعلى لإبراز النصوص
        gradient = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(gradient)
        for y in range(image.size[1]):
            draw.line([(0, y), (image.size[0], y)], fill=int(215 * (y / max(1, image.size[1] - 1)) ** 1.6))
        image = Image.composite(Image.new("RGB", image.size, (0x2A, 0x12, 0x3E)), image, gradient)
        save_jpeg(image, os.path.join(BACKGROUNDS, job["name"]), quality=80)


# ----------------------------------------------------------------------------
# 3) صورة شخصية بديلة (Monogram Placeholder)
# ----------------------------------------------------------------------------
def build_profile_placeholder():
    """
    توليد صورة شخصية بديلة أنيقة (Monogram) — لا تُستخدم صورة وجه حقيقية.

    ملاحظة مهمة: لا تُطبع أي أسماء ملفات أو مسارات أو تعليمات داخل الصورة،
    لأن الصورة معروضة للزائر داخل قسم «من أنا»، وأي نص مسار فيها يظهر
    كعيب بصري واضح. تعليمات الاستبدال موجودة في README.txt فقط.
    """
    print("\n== الصورة الشخصية البديلة ==")
    width, height = 1000, 1250
    canvas = Image.new("RGB", (width, height), CREAM_PEARL)
    draw = ImageDraw.Draw(canvas)

    # تدرّج قطري ناعم (وردي عاجي)
    for y in range(height):
        ratio = y / height
        color = tuple(int(CREAM_PEARL[i] + (BLUSH_MIST[i] - CREAM_PEARL[i]) * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)

    # هالات وردية/بنفسجية ناعمة
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.ellipse([width // 2 - 440, height // 2 - 480, width // 2 + 440, height // 2 + 400],
                  fill=(0xE9, 0xA7, 0xB0, 78))
    odraw.ellipse([width // 2 - 310, height // 2 - 350, width // 2 + 310, height // 2 + 270],
                  fill=(0x8E, 0x55, 0x78, 46))
    odraw.ellipse([width // 2 - 170, height // 2 - 200, width // 2 + 170, height // 2 + 140],
                  fill=(0xE2, 0xC0, 0x8D, 40))
    overlay = overlay.filter(ImageFilter.GaussianBlur(80))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # حلقات معدنية متداخلة
    for index, radius in enumerate((430, 330, 235, 140)):
        offset = index * 15
        draw.ellipse(
            [width // 2 - radius + offset, height // 2 - radius + offset,
             width // 2 + radius - offset, height // 2 + radius - offset],
            outline=METALLIC if index % 2 == 0 else (0xB3, 0xA4, 0x97),
            width=3,
        )

    # نقاط ضوء صغيرة
    for gx in range(80, width, 96):
        for gy in range(80, height, 96):
            draw.ellipse([gx, gy, gx + 3, gy + 3], fill=(0xE9, 0xA7, 0xB0))

    # --- Monogram "H" أنيق (حرف واحد فقط، بدون أي نص أو مسار ملفات) ---
    cx, cy = width // 2, height // 2 - 30
    try:
        from PIL import ImageFont
        mono_font = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 420)
    except Exception:  # noqa: BLE001
        mono_font = None

    if mono_font is not None:
        # طبقة ظل شامبانيا خفيفة تعطي عمقًا معدنيًا
        draw.text((cx + 7, cy + 9), "H", fill=(0xE2, 0xC0, 0x8D), anchor="mm", font=mono_font)
        draw.text((cx, cy), "H", fill=(0x5A, 0x27, 0x40), anchor="mm", font=mono_font)
    else:
        # بديل هندسي في حال عدم توفر الخط
        bar_w, bar_h = 26, 250
        left_x, right_x = cx - 96, cx + 96
        draw.rectangle([left_x - bar_w // 2, cy - bar_h // 2,
                        left_x + bar_w // 2, cy + bar_h // 2], fill=BERRY)
        draw.rectangle([right_x - bar_w // 2, cy - bar_h // 2,
                        right_x + bar_w // 2, cy + bar_h // 2], fill=BERRY)
        draw.rectangle([left_x - bar_w // 2, cy - 14,
                        right_x + bar_w // 2, cy + 14], fill=CHAMPAGNE)

    # --- خط توقيع زخرفي أسفل المونوغرام ---
    flourish = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    fdraw = ImageDraw.Draw(flourish)
    fdraw.arc([cx - 190, cy + 150, cx + 190, cy + 230], start=200, end=340,
              fill=(0xC9, 0x7C, 0x8C, 190), width=3)
    fdraw.arc([cx - 140, cy + 172, cx + 140, cy + 232], start=205, end=335,
              fill=(0xE2, 0xC0, 0x8D, 150), width=2)
    flourish = flourish.filter(ImageFilter.GaussianBlur(0.4))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), flourish).convert("RGB")

    save_jpeg(canvas, os.path.join(IMG, "profile.jpg"), quality=90)


# ----------------------------------------------------------------------------
# 4) أنماط هندسية + Favicon
# ----------------------------------------------------------------------------
def build_patterns_and_favicon():
    print("\n== الأنماط الهندسية و Favicon ==")
    # Pattern: شبكة لافندر خفيفة شفافة
    size = 600
    pattern = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(pattern)
    for x in range(0, size, 40):
        draw.line([(x, 0), (x, size)], fill=(0xC9, 0xB8, 0xF0, 30), width=1)
    for y in range(0, size, 40):
        draw.line([(0, y), (size, y)], fill=(0xC9, 0xB8, 0xF0, 30), width=1)
    for cx, cy in ((0, 0), (size, 0), (0, size), (size, size)):
        draw.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(0xC9, 0xB8, 0xF0, 80))
    save_png(pattern, os.path.join(BACKGROUNDS, "pattern-grid.png"))

    # Favicon: مربع بنفسجي عميق بحروف HADEEL فضية
    icon = Image.new("RGBA", (256, 256), PURPLE + (255,))
    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle([10, 10, 246, 246], radius=52, outline=SILVER, width=6)
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 76)
        draw.text((128, 134), "H", fill=(0xFA, 0xF9, 0xFD), anchor="mm", font=font)
    except Exception:  # noqa: BLE001
        draw.rectangle([100, 90, 156, 180], fill=(0xFA, 0xF9, 0xFD))
    save_png(icon, os.path.join(ROOT, "favicon.png"))


# ----------------------------------------------------------------------------
def main():
    print("=" * 68)
    print("  HA-Digital-Portfolio  |  توليد الصور والأصول")
    print("=" * 68)
    steps = [
        ("المشاريع", build_projects),
        ("الخلفيات", build_backgrounds),
        ("الصورة الشخصية البديلة", build_profile_placeholder),
        ("الأنماط والأيقونة", build_patterns_and_favicon),
    ]
    for title, func in steps:
        try:
            func()
        except Exception as error:  # noqa: BLE001
            print("  [!!] فشل قسم %s: %s" % (title, error))
    print("\nتم الانتهاء من توليد الأصول.\n")


if __name__ == "__main__":
    sys.exit(main())
