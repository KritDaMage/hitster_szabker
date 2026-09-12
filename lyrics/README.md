# Dalszövegek

Ide kerülnek a Szabker dicsi módhoz tartozó teljes dalszövegek, egy fájl daláként.

## Fájlnév

`<track ID>.json` — ugyanaz a 22 karakteres track ID, amit a QR-kódoknál és a
gyökérbeli `Worship.txt`-ben is használunk (a Spotify-megosztólink végén van).

**A fájlnév az azonosító, nem csak elnevezés.** Ez köti a szöveget a dalhoz,
ezért ha a `Worship.txt`-ben track ID-t írsz át, ezt a fájlt is át kell nevezni
(és benne a `track_id` mezőt). A `tools/generate_cards.py` figyelmeztet, ha egy
`+` jelölt sorhoz nincs fájl, vagy ha egy fájlhoz nincs sor.

Példa: `4uLU6hMCjMI75M1A2tKUQC.json`

## Formátum

Egy objektum, benne pár opcionális fejléc-mező és a szakaszok tömbje, a dal
tényleges sorrendjében. Egy ismétlődő refrén többször is szerepelhet a
listában — ott, ahol a dalban ténylegesen elhangzik.

```json
{
  "track_id": "4uLU6hMCjMI75M1A2tKUQC",
  "youtube": "",
  "title": "Magyar cím",
  "original_title": "Original Title",
  "author": "Eredeti szerző / előadó",
  "translator": "Kovács János",
  "sections": [
    { "type": "verse", "text": "első sor\nmásodik sor\nharmadik sor" },
    { "type": "chorus", "text": "refrén első sora\nrefrén második sora" },
    { "type": "verse", "text": "..." },
    { "type": "chorus", "text": "..." },
    { "type": "bridge", "text": "..." }
  ]
}
```

- `track_id`: a fájlnévvel megegyező 22 karakteres track ID, csak kényelmi
  célból (pl. hogy egy YouTube-link listát könnyebben be lehessen párosítani
  a megfelelő fájlhoz) — az app nem használja, mert a fájlnévből amúgy is
  tudja.
- `youtube`: opcionális, egy YouTube-videó a dalhoz (pl. eredeti előadás vagy
  lyric video). Elfogadja a csupasz 11 karakteres videó ID-t, vagy egy teljes
  linket (`youtube.com/watch?v=...`, `youtu.be/...`, `youtube.com/embed/...`).
  Ha azt szeretnéd, hogy ne az elejétől induljon, illeszd be a YouTube
  „Megosztás” → „adott ponttól” linkjét, vagy a lejátszó jobb klikkjéből az
  „URL másolása az aktuális időponttól” opciót — a link végén lévő `?t=93`
  (másodperc) vagy `?t=1m33s` alakot az app automatikusan felismeri és onnan
  indítja a videót. **Egyelőre csak fejlesztői módban (`?mock=1`) jelenik meg**,
  kattintásra töltődik be (nincs automatikus iframe/lekérés) — élesben a mezőt
  az app figyelmen kívül hagyja. Ha `versions` van használatban, mindegyik
  verzió kaphat saját `youtube` mezőt (ugyanúgy, mint a `title`/`translator`/stb.).
- `title`, `original_title`, `author`, `translator`: mind opcionális. Ha
  kitöltöd őket, ezek jelennek meg a dalszöveg-nézet tetején — ha nem, az app
  visszaesik a Spotifytól kapott (és a gyökérbeli `Worship.txt`-ben megadott)
  címre, előadóra.
- `type`: rövid angol szó, ami a nézetben szó szerint megjelenik címkeként —
  ezért érdemes a dal tényleges szerkezetét leírni, nem csak a legközelebbi
  ismert kategóriát ráhúzni. Gyakori értékek:
  - `"intro"` — hangszeres/szöveg nélküli bevezető
  - `"verse"` (versszak) — a történetet viszi előre, versszakonként más szöveg
  - `"pre-chorus"` (előkórus) — rövid átvezető a versszak és a refrén között;
    jellemzően többször is előfordul, és mindig ugyanabba a refrénbe torkollik
  - `"chorus"` (refrén) — a dal visszatérő magja, szövege általában azonos
  - `"bridge"` (híd) — a dal közepe felé egyszer előforduló, a többitől
    harmóniában/dallamban eltérő rész — **ne keverd össze az előkórussal**:
    a bridge egyedi és kontrasztos, az előkórus ismétlődik és a refrénhez vezet
  - `"outro"` — záró rész, ami nem ismétlődő refrén és nem is önálló bridge
  - `"tag"` — ha van egy külön, formailag elváló, rövid záró/ismétlő rész a végén

  Ha egyik sem illik pontosan, bármi más rövid angol szó is használható —
  a lényeg, hogy a címke a szakasz valódi szerepét tükrözze, ne a legutóbb
  használt sablont.
- `text`: a szakasz sorai, `\n`-nel elválasztva.

Ha egy dalhoz nincs itt fájl, a „Dalszöveg" gomb egyszerűen nem jelenik meg
felfedéskor — nem kell mindegyikhez azonnal elkészíteni.

## Több fordítás egy dalhoz

Ha egy dalnak több, egymástól független magyar fordítása is létezik, ne írd
felül az egyiket a másikkal — tedd fel mindkettőt egy `versions` tömbbe. Egy
`versions`-elem pontosan ugyanolyan alakú, mint eddig maga a fájl volt
(`title`, `original_title`, `author`, `translator`, `sections`):

```json
{
  "versions": [
    { "translator": "Első fordító", "sections": [ ... ] },
    { "translator": "Második fordító", "sections": [ ... ] }
  ]
}
```

Ha `versions` van jelen, az app lapozó gombokat (‹ ›) jelenít meg a
dalszöveg fejlécében, és mindig az éppen kiválasztott elem `title`/
`original_title`/`author`/`translator`/`sections` mezőit használja — a
`title`/`original_title`/`author`/`translator`/`sections` mezőket ilyenkor
a legfelső szinten nem kell (és nem is szabad) kitölteni, csak a
`versions` elemein belül. Ha egy dalnak csak egy fordítása van, maradhat a
régi, lapos formátum (`versions` nélkül) — nem kötelező áttérni.

## A dalkatalógus

A menü „Szabker dicsi" módban megjelenő „Dalkatalógus" gombja a gyökérbeli
`Worship.txt`-ből épül fel: minden **csillagos** (`*`) sor bekerül, és a sor
**első oszlopa** (`+`) mondja meg, hogy van-e a dalhoz szöveg. Így a katalógus
azokat a dalokat is felsorolja, amikhez még nincs dalszöveg — azok halványabb
sorként jelennek meg.

**Új dalszöveg felvételekor nincs külön nyilvántartás, amibe át kell vezetni:**
elég kitenni a `+` jelet a `Worship.txt` megfelelő sorába. A track ID köti össze
a kettőt.

> Korábban volt itt egy `index.json`, és egy `0000000000000000000000.json` mock
> fixtúra is. **Mindkettő megszűnt** (2026 szeptember): az `index.json` a
> `Worship.txt` kézzel karbantartott másolata volt, és elcsúszott tőle; a mock
> fixtúra helyett a fejlesztői mód (`?mock=1`) most a valódi listából húz egy
> véletlen dalt. Ne hozd vissza egyiket sem.
