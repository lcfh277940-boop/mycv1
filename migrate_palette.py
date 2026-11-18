# -*- coding: utf-8 -*-
"""
HA-Digital-Portfolio / tools/migrate_palette.py
------------------------------------------------------------------
ترحيل لوحة الألوان من (Lavender & Silver) إلى هوية جديدة:
«Rose Quartz & Champagne Luxury».

الهوية الجديدة:
    Berry (عميق)      #5A2740   — العناوين والنصوص الأساسية
    Berry Deep        #3F1A30
    Mauve Plum        #8E5578
    Soft Rose         #E9A7B0   — اللون المميّز الأساسي
    Rose Deep         #C97C8C
    Champagne         #E2C08D   — اللمسات الذهبية الراقية
    Metallic Silver   #D3C6BC   — الحدود المعدنية
    Cream Pearl       #FDF8F4   — الخلفية
    Blush Mist        #F8E9EA   — الخلفيات الثانوية
    Warm Mist         #EFE4E6

يقوم السكربت باستبدال كل القيم اللونية داخل style.css ويحدّث
أسماء متغيّرات CSS لتطابق الهوية الجديدة.
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(ROOT, "style.css")

# ---------------------------------------------------------------------------
# 1) خريطة القيم السداسية (من القديمة إلى الجديدة)
# ---------------------------------------------------------------------------
HEX_MAP = {
    # --- البرقوقي / البنفسجي العميق -> التوت العميق ---
    "#542B78": "#5A2740",
    "#3D1D5A": "#3F1A30",
    "#2E1446": "#34182B",
    "#33184E": "#3A1C32",
    "#241038": "#2A1226",
    "#2F1348": "#38182C",
    "#6E4B9E": "#8E5578",
    "#6E3C96": "#7E4A6C",
    "#7C4BA8": "#96597C",
    "#7E5BB0": "#A96A8C",
    "#8E6FC9": "#C97C8C",
    "#9A7CCB": "#D192A4",
    "#B49BE4": "#DCA3AE",
    "#D8C9F6": "#F3D0D5",
    "#C9B8F0": "#E9A7B0",
    "#EDE6FA": "#F8E9EA",
    "#A98FDD": "#DE9FB4",
    "#D9C9F8": "#EFC6CE",
    "#DCE7F5": "#F2E6E4",
    # --- الفضي -> معدني دافئ ---
    "#C8CDD6": "#D3C6BC",
    "#9BA4B3": "#B3A497",
    "#AFB7C4": "#C4B5AA",
    "#C6CEDA": "#D9CCC2",
    "#DDE3EB": "#E8DCD4",
    "#E6E9F0": "#EADFD8",
    "#E6E9F6": "#EEE2E2",
    "#79838F": "#8A7B74",
    # --- ألوان الأكواد ---
    "#4E86C7": "#C0796F",
    "#5B7FB0": "#B0857F",
    "#9FB6DC": "#D9A9AE",
    "#9FC6FF": "#F0B8C4",
    "#6E6A78": "#75666C",
    "#A79BB8": "#A8969C",
    # --- النصوص ---
    "#2A2135": "#33202B",
    "#524A5E": "#5C4950",
    "#8A8396": "#94838A",
    # --- الخلفيات الفاتحة ---
    "#FAF9FD": "#FDF8F4",
    "#FBFAFE": "#FEFAF8",
    "#FCFBFE": "#FEFBF9",
    "#F7F5FC": "#FCF7F4",
    "#F7F4FC": "#FBF3F3",
    "#F6F4FC": "#FAF0F1",
    "#F6F2FC": "#F9EEEE",
    "#F4F0FB": "#F8ECED",
    "#F4F7FC": "#FAF3F1",
    "#F4F7FB": "#FAF3F1",
    "#F3F6FC": "#FAF4F2",
    "#F3EFFA": "#F7ECEE",
    "#F2EEFA": "#F7EBEC",
    "#F1ECF9": "#F7EDEE",
    "#F1ECFA": "#F6E9EA",
    "#F8F6FD": "#FCF6F4",
    "#EFF3FB": "#F5EBEA",
    "#D9D3E4": "#E7D5D8",
    "#D3C8E4": "#E3D2D5",
    # --- الوضع الليلي ---
    "#140C1E": "#1A0E15",
    "#120B1C": "#180C13",
    "#151021": "#1D0F17",
    "#161021": "#1E1019",
    "#161022": "#1E1119",
    "#161227": "#1E121A",
    "#170E24": "#1D1019",
    "#180F24": "#1E1119",
    "#181026": "#1F111A",
    "#181029": "#20111B",
    "#191026": "#21121C",
    "#1A1026": "#23131E",
    "#1A1027": "#23131E",
    "#1A1129": "#24141F",
    "#1B1129": "#251520",
    "#1C1230": "#271622",
    "#1D1229": "#281723",
    "#241734": "#2C1A28",
    "#281B39": "#301D2B",
}

# ---------------------------------------------------------------------------
# 2) خريطة قيم RGBA / RGB (نفسTriple مع مسافات أو بدونها)
# ---------------------------------------------------------------------------
TRIPLE_MAP = [
    ("142, 111, 201", "201, 124, 140"),
    ("142,111,201", "201,124,140"),
    ("201, 184, 240", "233, 167, 176"),
    ("201,184,240", "233,167,176"),
    ("84, 43, 120", "90, 39, 64"),
    ("84,43,120", "90,39,64"),
    ("61, 29, 90", "90, 39, 64"),
    ("61,29,90", "90,39,64"),
    ("46, 20, 70", "63, 26, 48"),
    ("46,20,70", "63,26,48"),
    ("220,231,245", "243, 226, 224"),
    ("237,230,250", "248, 233, 234"),
    ("240,235,252", "247, 237, 236"),
    ("246,243,252", "253, 246, 243"),
    ("250,249,253", "253, 248, 244"),
    ("200, 205, 214", "211, 198, 188"),
    ("200,205,214", "211,198,188"),
    ("155, 164, 179", "179, 164, 151"),
    ("241, 236, 249", "248, 240, 238"),
    ("241,236,249", "248,240,238"),
    ("20,12,30", "26, 14, 21"),
    ("22,10,34", "28, 15, 23"),
    ("30,14,46", "37, 20, 30"),
    ("36, 20, 52", "44, 24, 36"),
    ("38, 24, 53", "46, 28, 39"),
    ("38,16,58", "46, 22, 35"),
    ("40, 20, 58", "48, 25, 37"),
    ("45, 30, 62", "53, 34, 45"),
    ("45,30,62", "53,34,45"),
    ("16,7,26", "21, 12, 17"),
    ("90,120,180", "170, 120, 130"),
]

# ---------------------------------------------------------------------------
# 3) إعادة تسمية متغيّرات CSS لتطابق الهوية الجديدة
#    (الترتيب مهم: الأطول أولًا)
# ---------------------------------------------------------------------------
TOKEN_MAP = [
    ("--lavender-dim", "--rose-soft"),
    ("--silver-line", "--metallic-line"),
    ("--silver-deep", "--metallic-deep"),
    ("--purple-deep", "--berry-deep"),
    ("--lavender", "--rose"),
    ("--purple", "--berry"),
    ("--lilac", "--blush"),
    ("--silver", "--metallic"),
    ("--pearl", "--cream"),
    ("--blue-light", "--mist"),
]


def migrate(text):
    # 1) القيم السداسية
    for old, new in HEX_MAP.items():
        text = re.sub(re.escape(old) + r"(?![0-9A-Fa-f])", new, text, flags=re.IGNORECASE)

    # 2) قيم RGBA / RGB
    for old, new in TRIPLE_MAP:
        text = text.replace("rgba(" + old, "rgba(" + new)
        text = text.replace("rgb(" + old, "rgb(" + new)

    # 3) إعادة تسمية المتغيّرات
    for old, new in TOKEN_MAP:
        text = text.replace(old, new)

    return text


def main():
    with io.open(CSS, "r", encoding="utf-8") as handle:
        css = handle.read()

    before = len(re.findall(r"#[0-9A-Fa-f]{6}", css))
    css = migrate(css)
    after = len(re.findall(r"#[0-9A-Fa-f]{6}", css))

    # 4) تحديث قيم متغيّرات الهوية الأساسية يدويًا لضمان الدقة
    css = css.replace(
        "--rose:    #E9A7B0;   /* Lavender */",
        "--rose:    #E9A7B0;   /* Soft Rose */")
    css = css.replace(
        "--berry:      #5A2740;   /* Deep Purple */",
        "--berry:      #5A2740;   /* Deep Berry */")
    css = css.replace(
        "--blush:       #F8E9EA;   /* Soft Lilac */",
        "--blush:       #F8E9EA;   /* Blush Mist */")
    css = css.replace(
        "--metallic:      #C8CDD6;   /* Silver */",
        "--metallic:      #D3C6BC;   /* Metallic Silver */")
    css = css.replace(
        "--cream:       #FDF8F4;   /* Pearl White */",
        "--cream:       #FDF8F4;   /* Cream Pearl */")
    css = css.replace(
        "--mist:  #F2E6E4;   /* Light Blue */",
        "--mist:  #EFE4E6;   /* Warm Mist */")

    with io.open(CSS, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(css)

    print("تمت ترحيل لوحة الألوان إلى هوية Rose Quartz & Champagne.")
    print("عدد القيم السداسية قبل: %d  |  بعد: %d" % (before, after))

    # تحقق: عدم بقاء أي لون قديم
    leftovers = []
    for old in list(HEX_MAP.keys()) + ["#C9B8F0", "#542B78", "#EDE6FA", "#C8CDD6", "#DCE7F5", "#FAF9FD"]:
        if re.search(re.escape(old) + r"(?![0-9A-Fa-f])", css, flags=re.IGNORECASE):
            leftovers.append(old)
    print("بقايا قديمة: %s" % (", ".join(leftovers) if leftovers else "لا شيء ✔"))


if __name__ == "__main__":
    sys.exit(main())
