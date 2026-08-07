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
- `type`: `"verse"` (versszak), `"chorus"` (refrén), `"bridge"` (híd) — vagy
  bármi más rövid angol szó (pl. `"coda"`), ha egy szakasz nem illik ebbe a
  három kategóriába; ilyenkor a nézet egyszerűen ezt a szót írja ki címkeként.
- `text`: a szakasz sorai, `\n`-nel elválasztva.

Ha egy dalhoz nincs itt fájl, a „Dalszöveg" gomb egyszerűen nem jelenik meg
felfedéskor — nem kell mindegyikhez azonnal elkészíteni.
