# Data Importer Cloud Run

Ez a minta Cloud Run service Pub/Sub push üzenetet fogad egy Cloud Storage file upload után.

A feldolgozást BigQuery config tábla vezérli. A kód nem fixen egy fájlnévre vagy egy Excel sheetre van megírva, hanem a config alapján dönti el:

- melyik fájlmintára reagáljon,
- CSV vagy Excel formátumot várjon,
- Excel esetén melyik sheetet olvassa,
- melyik BigQuery RAW táblába töltsön,
- append vagy truncate módban töltsön,
- milyen oszlopokat várjon el,
- milyen BigQuery sémával hozza létre a cél RAW táblát,
- adjon-e technikai metadata oszlopokat a RAW rekordokhoz.

## Folder flow

```text
landing/
   új fájlok

processed/
   sikeresen feldolgozott fájlok

archive/
   sikeres feldolgozás után megtartott eredeti másolat

error/
   sikertelen vagy ismeretlen configú fájlok
```

## Cloud Run environment variables

```text
PROJECT_ID=ford-training-430008
CONFIG_DATASET=training_config
CONFIG_TABLE=file_ingestion_config
RUN_LOG_TABLE=file_ingestion_run_log
LANDING_PREFIX=landing/
PROCESSED_PREFIX=processed/
ARCHIVE_PREFIX=archive/
ERROR_PREFIX=error/
ARCHIVE_SUCCESS_COPY=true
```

## Pub/Sub message

A service Pub/Sub push envelope-ot vár. A `message.data` mezőben a Cloud Storage notification JSON szerepel base64 kódolva.

Minimális példa dekódolt tartalomra:

```json
{
  "bucket": "my-training-bucket",
  "name": "landing/sales_data.csv"
}
```

## Config modell

Egy config sor egy file pattern és egy cél RAW tábla közötti megfeleltetés.

Excel fájloknál egy fájlhoz több config sor is tartozhat, például:

```text
landing/monthly_input.xlsx + Sales sheet   -> janos_raw.sales
landing/monthly_input.xlsx + Dealers sheet -> janos_raw.dealer_master
```

CSV esetén a `sheet_name` értéke `NULL`.

## Ki hozza létre a RAW táblákat?

A minta program a config tábla `target_schema` oszlopa alapján létrehozza a cél BigQuery táblát, ha az még nem létezik.

Példa config részlet:

```sql
[
  STRUCT("dealer_code" AS column_name, "STRING" AS data_type, "NULLABLE" AS mode),
  STRUCT("market" AS column_name, "STRING" AS data_type, "NULLABLE" AS mode)
]
```

Az importer ehhez automatikusan hozzáadja a technikai oszlopokat is:

```text
_source_bucket
_source_object
_ingestion_config_id
_ingested_at_utc
```

Ha nincs `target_schema`, akkor a program BigQuery autodetect módra vált. A tréningben viszont a config-alapú séma a javasolt út, mert így látható, hogy a betöltés nem Python kód módosításával, hanem konfigurációval vezérelhető.

## Sample Excel létrehozása

A repositoryban CSV minták vannak, és adtunk mellé egy kis segédscriptet is.

Ha lokálisan telepítve vannak a `requirements.txt` csomagjai, akkor ebből létrehozható egy két sheetes Excel:

```bash
python create_sample_excel.py
```

Az eredmény:

```text
samples/monthly_sales.xlsx
```

## Ismeretlen fajl

Ha a feltöltött fájlra nincs engedélyezett config sor, akkor a service:

- nem tölti be BigQuery-be,
- átmozgatja az `error/` folderbe,
- `UNKNOWN_CONFIG` statusszal logolja a futást.

Ez szándékos. Jobb megállítani az ismeretlen inputot, mint csendben rossz táblába tölteni.

## Miért kell idempotencia?

A Pub/Sub legalább egyszer kézbesítési modellt használ. Ez azt jelenti, hogy ugyanaz az üzenet ritka esetben többször is megérkezhet, főleg akkor, ha a Cloud Run service hibával tér vissza.

Ezért az importer a run logban ellenőrzi, hogy ugyanaz a Cloud Storage objektum és generáció sikeresen feldolgozódott-e már.

Ha igen, akkor a duplikált üzenetet nem tölti be újra:

```text
duplicate_ignored
```

Fontos eset: ha a BigQuery betöltés sikerült, de az eredeti fájl `processed/` folderbe mozgatása hibára fut, a service nem ad vissza 500-as hibát. Ilyenkor `SUCCESS_MOVE_FAILED` státuszt logol, és 200-as választ ad a Pub/Subnak.

Ennek oka, hogy egy Pub/Sub retry újra elindítaná a teljes feldolgozást, ami append típusú RAW tábláknál duplikált sorokat okozhatna.
