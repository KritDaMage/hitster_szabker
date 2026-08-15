"""
Hitster Szabker kartyagenerator.

Beolvassa a source/Worship.txt-t, kiszedi a csillaggal (*) jelolt sorokat
(azokat, amikhez mar van magyar cim), es egy nyomtatasra kesz HTML-t general:
minden dalhoz egy "domino" alaku egyseget, benne egymas mellett a QR-kod
(bal fel) es az evszam+cim (jobb fel). A jobb felet hatrahajtva a ket fel
egyetlen ketoldalas kartyat ad - nincs sziksieg kettoldalas nyomtatasra.

Hasznalat:
    python tools/generate_cards.py

A kimenet a tools/output/cards.html -be kerul. Nyisd meg bongeszoben,
es Ctrl+P -> mentes PDF-kent / nyomtatas (egyoldalas eleg).
Kivagas: a szaggatott vonal menten vagd ki a domino alaku egyseget, majd
a folytonos vonal menten hajtsd hatra a jobb (evszamos) felet, ugy hogy
mindket nyomtatott oldal kifele nezzen.
"""

import base64
import io
import math
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw
from pyzbar.pyzbar import decode as zbar_decode
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = ROOT / "source" / "Worship.txt"
OUTPUT_FILE = ROOT / "tools" / "output" / "cards.html"
LOGO_FILE = ROOT / "szabker_budapest_ifi.svg"
APP_BASE_URL = "https://kritdamage.github.io/hitster_szabker/"

# a logo finom vonalai (a kurziv felirat) a QR-modulok felbontasanal
# kisebb leptekben "zajt" okozhatnak, ami bizonyos meretnel/pozicional
# megtoheti a beolvashatosagot - ezert minden egyes QR-t tenylegesen
# ledekodolunk generalas kozben, es ha a celzott meret nem olvashato,
# fokozatosan kisebbre vesszuk a logot, vegso esetben logo nelkul hagyjuk
# a meret/olvashatosag kapcsolata nem fokozatos, hanem kaotikus (finom
# alias-hatas a logo reszletei es a QR-modulracs kozott) - 6.8% korul van
# egy szuk, de az osszes jelenlegi dalra leellenorzott biztonsagos sav,
# ez az elsodleges cel; ha egy jovobeli uj dal itt nem menne at, a
# tartalek lista also, mar korabban is biztonsagosnak talalt ertekei felé
# lepked
LOGO_COVERAGE = 0.068
LOGO_FALLBACK_COVERAGES = [0.068, 0.065, 0.055, 0.045, 0.035, 0.03, 0.0]
LOGO_RING_MARGIN = 0.18  # feher gyuru szelessege a logo sugarahoz kepest

# A4, mm
PAGE_W_MM = 210
PAGE_H_MM = 297
MARGIN_MM = 5  # a legtobb nyomtato ennel keskenyebb margot nem tud
EDGE_INSET_MM = 3  # a vagasjelek ennyivel maradjanak beljebb a lap szelenel

# Egy kartyafel (negyzet) kb. ekkora legyen (mm), de a script ehhez kepest
# keresi meg a pontos meretet, ami a legtobb egyseget engedi kiferni
# veszteseg nelkul. Egy egyseg (domino) 2x ekkora szeles, mint magas.
SIZE_SEARCH_RANGE_MM = (45, 55)

# hatoldali motivum: evszamonkent kicsit mas alaku, amorf blob, ami a
# kartya szelen belogva levagodik
MIN_K, MAX_K = 3, 8
MOTIF_N_POINTS = 40
MOTIF_SCALE = 1.4


def hash01(n):
    h = (n * 2654435761) & 0xFFFFFFFF
    return (h % 10000) / 10000


def motif_points(year, min_year, max_year, cx, cy, radius):
    seed = year * 97
    t = (year - min_year) / (max_year - min_year) if max_year > min_year else 0
    k = min(MIN_K + int(t * (MAX_K - MIN_K + 1)), MAX_K)
    a = 0.08 + hash01(seed * 13) * 0.10
    phi = hash01(seed * 31) * 2 * math.pi
    pts = []
    for i in range(MOTIF_N_POINTS):
        theta = 2 * math.pi * i / MOTIF_N_POINTS
        r = 1 + a * math.cos(k * theta + phi)
        x = cx + radius * r * math.cos(theta)
        y = cy + radius * r * math.sin(theta)
        pts.append((x, y))
    return pts


def smooth_path(pts):
    # Catmull-Rom -> kubikus Bezier, zart gorbe - ez adja az amorf,
    # lekerekitett blob-format a sokszog-csucsok helyett
    n = len(pts)
    d = f"M {pts[0][0]:.1f},{pts[0][1]:.1f} "
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1x, c1y = p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6
        c2x, c2y = p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6
        d += f"C {c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {p2[0]:.1f},{p2[1]:.1f} "
    return d + "Z"


def motif_svg(year, min_year, max_year):
    ang = hash01(year * 41) * 2 * math.pi
    cx = 50 + 40 * math.cos(ang)
    cy = 50 + 40 * math.sin(ang)
    pts = motif_points(year, min_year, max_year, cx, cy, 44 * MOTIF_SCALE)
    return f'<svg class="motif" viewBox="0 0 100 100"><path d="{smooth_path(pts)}"/></svg>'


def parse_songs():
    songs = []
    for line in SOURCE_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) < 3 or cols[1] != "*":
            continue
        hu_title, original_title, year, spotify_link = cols[2].split("|")
        track_id = spotify_link.strip().split("/")[-1].split("?")[0]
        songs.append({
            "hu_title": hu_title.strip(),
            "original_title": original_title.strip(),
            "year": year.strip(),
            "track_id": track_id,
        })
    return songs


def find_best_grid():
    usable_w = PAGE_W_MM - 2 * MARGIN_MM
    usable_h = PAGE_H_MM - 2 * MARGIN_MM
    lo, hi = SIZE_SEARCH_RANGE_MM
    best = None
    size = lo
    while size <= hi + 1e-9:
        cols = int(usable_w // (2 * size))  # domino = 2 negyzet szeles
        rows = int(usable_h // size)
        count = cols * rows
        waste = usable_w * usable_h - count * (2 * size) * size
        candidate = (count, -waste, size, cols, rows)
        if best is None or candidate[:2] > best[:2]:
            best = candidate
        size += 0.1
    count, _, size, cols, rows = best
    return round(size, 1), cols, rows


_logo_cache = None


def load_logo():
    # a logo egy majdnem szel-erintő kor (feher szoveggel benne) - a
    # negyzet sarkait kell csak atlatszova tenni, a kor belsejet
    # (a feher betuket is) opakan kell tartani, ezert geometriai
    # kormaszkot hasznalunk szin-alapu kivagas helyett
    global _logo_cache
    if _logo_cache is None:
        drawing = svg2rlg(str(LOGO_FILE))
        buf = io.BytesIO()
        renderPM.drawToFile(drawing, buf, fmt="PNG", bg=0xFFFFFF, dpi=300)
        buf.seek(0)
        img = Image.open(buf).convert("RGB")
        # a logo majdnem-fekete szine (#231f20) helyett tiszta feketet
        # hasznalunk, hogy pontosan illeszkedjen a QR sajat feketejehez
        bw = img.convert("L").point(lambda p: 0 if p < 128 else 255)
        img = Image.merge("RGB", (bw, bw, bw)).convert("RGBA")
        w, h = img.size
        radius = min(w, h) / 2
        cx, cy = w / 2, h / 2
        mask = Image.new("L", (w, h), 0)
        px = mask.load()
        for y in range(h):
            dy2 = (y + 0.5 - cy) ** 2
            for x in range(w):
                dx = x + 0.5 - cx
                px[x, y] = 255 if dx * dx + dy2 <= radius * radius else 0
        img.putalpha(mask)
        _logo_cache = img
    return _logo_cache


def _make_base_qr(url):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=2, box_size=16)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image().convert("RGBA")


def _is_scannable(img, expected_url):
    result = zbar_decode(img.convert("L"))
    return len(result) == 1 and result[0].data.decode("utf-8") == expected_url


def _white_ring(size):
    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([0, 0, size - 1, size - 1], fill=(255, 255, 255, 255))
    return ring


def make_qr_data_uri(track_id):
    url = f"{APP_BASE_URL}#{track_id}"
    logo = load_logo()

    for coverage in LOGO_FALLBACK_COVERAGES:
        img = _make_base_qr(url)
        if coverage > 0:
            logo_size = int(img.width * coverage ** 0.5)
            ring_size = int(logo_size * (1 + LOGO_RING_MARGIN))
            ring = _white_ring(ring_size)
            ring_pos = ((img.width - ring_size) // 2, (img.height - ring_size) // 2)
            img.paste(ring, ring_pos, ring)
            logo_r = logo.resize((logo_size, logo_size), Image.LANCZOS)
            pos = ((img.width - logo_size) // 2, (img.height - logo_size) // 2)
            img.paste(logo_r, pos, logo_r)
        if _is_scannable(img, url):
            if coverage != LOGO_COVERAGE:
                print(f"  megjegyzes: {track_id} - a logo {coverage*100:.0f}%-ra csokkentve, hogy olvashato maradjon")
            break
    else:
        # LOGO_FALLBACK_COVERAGES vegen 0.0 all, ami logo nelkuli sima QR -
        # az mindig olvashato, ide elvileg sose kellene eljutni
        img = _make_base_qr(url)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def build_html(songs, size_mm, cols, rows):
    per_page = cols * rows
    pages = [songs[i:i + per_page] for i in range(0, len(songs), per_page)]
    unit_w = 2 * size_mm
    years = [int(s["year"]) for s in songs if s["year"].isdigit()]
    min_year, max_year = min(years), max(years)

    page_blocks = []
    for page_songs in pages:
        rows_here = -(-len(page_songs) // cols)  # ceil
        grid_w = cols * unit_w
        grid_h = rows_here * size_mm
        offset_x = (PAGE_W_MM - grid_w) / 2
        if rows_here == rows:
            offset_y = (PAGE_H_MM - grid_h) / 2
        else:
            # hianyos utolso lap: a lap tetejere igazitva (ugyanaz a felso
            # margo, mint egy teli lapon), ne kozepre - a maradek ures
            # hely lent gyuljon ossze
            offset_y = (PAGE_H_MM - rows * size_mm) / 2

        units = []
        for i, song in enumerate(page_songs):
            qr = make_qr_data_uri(song["track_id"])
            motif = ""
            if song["year"].isdigit():
                motif = f'<div class="frame">{motif_svg(int(song["year"]), min_year, max_year)}</div>'
            units.append(
                '<div class="unit">'
                f'<div class="half front"><img src="{qr}" alt=""></div>'
                '<div class="half back">'
                f'{motif}'
                f'<div class="year">{song["year"]}</div>'
                '<div class="rule"></div>'
                f'<div class="title">{song["hu_title"]}</div>'
                '</div>'
                '</div>'
            )

        # Vagast segito jelek: csak a margoban (a kartyaracson kivul)
        # latszanak, ket rovid csonkban - a kartyak kozott nincs vonal,
        # de a ket csonk egy vonalzoval osszekothato a vagashoz. A csonkok
        # nem futnak ki a lap teteles szeleig, hogy a nyomtato biztosan
        # rakerekedjen az egesz jelre.
        grid_right = offset_x + grid_w
        grid_bottom = offset_y + grid_h
        lines = []
        for c in range(cols + 1):
            x = offset_x + c * unit_w
            top_len = offset_y - EDGE_INSET_MM
            if top_len > 0:
                lines.append(
                    f'<div class="cutline v" style="left:{x}mm; top:{EDGE_INSET_MM}mm; '
                    f'height:{top_len}mm;"></div>'
                )
            bottom_len = (PAGE_H_MM - EDGE_INSET_MM) - grid_bottom
            if bottom_len > 0:
                lines.append(
                    f'<div class="cutline v" style="left:{x}mm; top:{grid_bottom}mm; '
                    f'height:{bottom_len}mm;"></div>'
                )
        for r in range(rows_here + 1):
            y = offset_y + r * size_mm
            left_len = offset_x - EDGE_INSET_MM
            if left_len > 0:
                lines.append(
                    f'<div class="cutline h" style="top:{y}mm; left:{EDGE_INSET_MM}mm; '
                    f'width:{left_len}mm;"></div>'
                )
            right_len = (PAGE_W_MM - EDGE_INSET_MM) - grid_right
            if right_len > 0:
                lines.append(
                    f'<div class="cutline h" style="top:{y}mm; left:{grid_right}mm; '
                    f'width:{right_len}mm;"></div>'
                )

        grid_style = (
            f"left:{offset_x}mm; top:{offset_y}mm; "
            f"grid-template-columns: repeat({cols}, {unit_w}mm); "
            f"grid-template-rows: repeat({rows_here}, {size_mm}mm);"
        )
        page_blocks.append(
            f'<div class="page">'
            f'{"".join(lines)}'
            f'<div class="grid" style="{grid_style}">{"".join(units)}</div>'
            f'</div>'
        )

    return f"""<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8">
<title>Hitster Szabker kartyak</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800&display=swap&subset=latin,latin-ext" rel="stylesheet">
<style>
  @page {{ size: A4; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; }}
  .page {{
    position: relative;
    width: {PAGE_W_MM}mm;
    height: {PAGE_H_MM}mm;
    page-break-after: always;
    overflow: hidden;
  }}
  .cutline {{
    position: absolute;
    border: none;
  }}
  .cutline.v {{
    border-left: 1px solid #999;
  }}
  .cutline.h {{
    border-top: 1px solid #999;
  }}
  .grid {{
    position: absolute;
    display: grid;
  }}
  .unit {{
    display: flex;
    width: {2 * size_mm}mm;
    height: {size_mm}mm;
  }}
  .half {{
    width: {size_mm}mm;
    height: {size_mm}mm;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
  }}
  .half.front img {{ width: 82%; height: 82%; }}
  .half.back {{
    flex-direction: column;
    padding: 3mm;
    overflow: hidden;
    position: relative;
  }}
  .half.back .frame {{
    position: absolute;
    inset: 2mm;
    overflow: hidden;
    z-index: 0;
  }}
  .half.back .motif {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    opacity: .16;
  }}
  .half.back .motif path {{ fill: #000; }}
  .half.back .year {{
    position: relative;
    z-index: 1;
    font-family: "Bricolage Grotesque", "Segoe UI", system-ui, -apple-system, sans-serif;
    font-size: 9mm;
    font-weight: 800;
    letter-spacing: -.035em;
    line-height: 1;
  }}
  .half.back .rule {{
    position: relative;
    z-index: 1;
    width: 40%;
    border-top: 0.4mm solid #000;
    margin: 1.5mm 0;
  }}
  .half.back .title {{
    position: relative;
    z-index: 1;
    font-family: "Bricolage Grotesque", "Segoe UI", system-ui, -apple-system, sans-serif;
    font-size: 4.4mm;
    font-weight: 400;
    line-height: 1.15;
  }}
  @media screen {{
    body {{ background: #ccc; }}
    .page {{ background: #fff; margin: 5mm auto; box-shadow: 0 0 4px rgba(0,0,0,.3); }}
  }}
</style>
</head>
<body>
{"".join(page_blocks)}
</body>
</html>
"""


def main():
    songs = parse_songs()
    size_mm, cols, rows = find_best_grid()
    per_page = cols * rows
    print(f"{len(songs)} csillagozott dal a forrasban.")
    print(f"Kartyafel merete: {size_mm}mm, egyseg: {2 * size_mm}x{size_mm}mm.")
    print(f"{cols} oszlop x {rows} sor = {per_page} kartya/lap.")
    print(f"Lapok szama: {-(-len(songs) // per_page)} (egyoldalas nyomtatas).")

    html = build_html(songs, size_mm, cols, rows)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Kesz: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
