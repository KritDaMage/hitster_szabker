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
from pathlib import Path

import qrcode

ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = ROOT / "source" / "Worship.txt"
OUTPUT_FILE = ROOT / "tools" / "output" / "cards.html"
APP_BASE_URL = "https://kritdamage.github.io/hitster_szabker/"

# A4, mm
PAGE_W_MM = 210
PAGE_H_MM = 297
MARGIN_MM = 5  # a legtobb nyomtato ennel keskenyebb margot nem tud
EDGE_INSET_MM = 3  # a vagasjelek ennyivel maradjanak beljebb a lap szelenel

# Egy kartyafel (negyzet) kb. ekkora legyen (mm), de a script ehhez kepest
# keresi meg a pontos meretet, ami a legtobb egyseget engedi kiferni
# veszteseg nelkul. Egy egyseg (domino) 2x ekkora szeles, mint magas.
SIZE_SEARCH_RANGE_MM = (45, 55)


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


def make_qr_data_uri(track_id):
    url = f"{APP_BASE_URL}#{track_id}"
    img = qrcode.make(url, border=2, box_size=8)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def build_html(songs, size_mm, cols, rows):
    per_page = cols * rows
    pages = [songs[i:i + per_page] for i in range(0, len(songs), per_page)]
    unit_w = 2 * size_mm

    page_blocks = []
    for page_songs in pages:
        rows_here = -(-len(page_songs) // cols)  # ceil
        grid_w = cols * unit_w
        grid_h = rows_here * size_mm
        offset_x = (PAGE_W_MM - grid_w) / 2
        offset_y = (PAGE_H_MM - grid_h) / 2

        units = []
        for i, song in enumerate(page_songs):
            qr = make_qr_data_uri(song["track_id"])
            units.append(
                '<div class="unit">'
                f'<div class="half front"><img src="{qr}" alt=""></div>'
                '<div class="half back">'
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
  }}
  .half.back .year {{
    font-family: "Bricolage Grotesque", "Segoe UI", system-ui, -apple-system, sans-serif;
    font-size: 9mm;
    font-weight: 800;
    letter-spacing: -.035em;
    line-height: 1;
  }}
  .half.back .rule {{
    width: 40%;
    border-top: 0.4mm solid #000;
    margin: 1.5mm 0;
  }}
  .half.back .title {{
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
