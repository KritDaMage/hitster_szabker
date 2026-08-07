# Dalszövegek

Ide kerülnek a Szabker dicsi módhoz tartozó teljes dalszövegek, egy fájl daláként.

## Fájlnév

`<track ID>.json` — ugyanaz a 22 karakteres track ID, amit a QR-kódoknál és a
`SZABKER_TITLES`-nél is használunk (a Spotify-megosztólink végén van).

Példa: `4uLU6hMCjMI75M1A2tKUQC.json`

## Formátum

Egy objektum, benne pár opcionális fejléc-mező és a szakaszok tömbje, a dal
tényleges sorrendjében. Egy ismétlődő refrén többször is szerepelhet a
listában — ott, ahol a dalban ténylegesen elhangzik.

```json
{
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

- `title`, `original_title`, `author`, `translator`: mind opcionális. Ha
  kitöltöd őket, ezek jelennek meg a dalszöveg-nézet tetején — ha nem, az app
  visszaesik a Spotifytól kapott (és a `SZABKER_TITLES`-ben megadott) címre,
  előadóra.
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
  - `"coda"` — ha van egy külön, formailag elváló zárókód a végén

  Ha egyik sem illik pontosan, bármi más rövid angol szó is használható —
  a lényeg, hogy a címke a szakasz valódi szerepét tükrözze, ne a legutóbb
  használt sablont.
- `text`: a szakasz sorai, `\n`-nel elválasztva.

Ha egy dalhoz nincs itt fájl, a „Dalszöveg" gomb egyszerűen nem jelenik meg
felfedéskor — nem kell mindegyikhez azonnal elkészíteni.

## `index.json` — a dalkatalógus

A menü „Szabker dicsi" módban megjelenő „Dalkatalógus" gombja ezt a fájlt
tölti be, hogy felsorolhassa az összes olyan dalt, amihez tényleges
dalszöveg-fájl készült — kártya beolvasása nélkül is böngészhető, és
mindegyik sor átvisz a saját dalszövegére.

Formátum: `{ id, title }` párok tömbje, a `title` a lyrics-fájl `title`
mezőjével egyezik meg:

```json
[
  { "id": "4uLU6hMCjMI75M1A2tKUQC", "title": "Magyar cím" }
]
```

**Amikor felveszel egy új `<track ID>.json` dalszöveg-fájlt, vedd fel ide is
egy sorral** — ez a két hely nincs automatikusan szinkronban, statikus
GitHub Pages hosting mellett nincs könyvtárlistázás, amiből az app magától
összeszedhetné. A `0000000000000000000000.json` mock fixtúrát szándékosan
NEM tartalmazza (azt az app `?mock=1` alatt kézzel fűzi hozzá).

## `0000000000000000000000.json`

Ez **nem** egy valódi dal — ez a fejlesztői mód (`?mock=1`) fixtúrája. A
`scan()` mock módban mindig a `"0".repeat(22)` track ID-t „olvassa be”
(`index.html`, `MOCK` blokk), így ez a fájl kell ahhoz, hogy a
dalszöveg-nézetet be lehessen tesztelni bejelentkezés nélkül. Ne töröld, és
ne írj bele valódi dalt — ha egy tényleges számot dolgozol fel, azt a saját
track ID-jával mentsd.
