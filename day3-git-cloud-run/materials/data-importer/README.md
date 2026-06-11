# Data Importer Cloud Run

Ez a mappa egy konfigurációvezérelt Cloud Run importert tartalmaz.

A service célja, hogy a Cloud Storage `landing/` folderébe érkező fájlokat automatikusan feldolgozza, és a BigQuery RAW rétegbe töltse.

---

# Magas szintű működés

```text
User / Business team
        |
        | file upload
        v
Cloud Storage bucket
landing/
        |
        | OBJECT_FINALIZE notification
        v
Pub/Sub topic
        |
        | push subscription
        v
Cloud Run Data Importer
        |
        | reads config
        v
BigQuery config table
        |
        | load data
        v
BigQuery RAW tables
```

A Python kód nem konkrét fájlnevekre van írva. Azt, hogy egy fájllal mit kell csinálni, a BigQuery config tábla mondja meg.

---

# Folder flow

A bucketben négy logikai foldert használunk:

```text
landing/
  ide érkeznek az új fájlok

processed/
  ide kerülnek a sikeresen feldolgozott fájlok

archive/
  ide kerül egy sikeres feldolgozás utáni biztonsági másolat

error/
  ide kerülnek az ismeretlen vagy hibás fájlok
```

Cloud Storage-ban ezek technikailag nem valódi mappák, hanem objektumnév-prefixek. A `.keep` fájl csak arra szolgál, hogy az üres prefixek is látszódjanak a Console felületén.

Sikeres feldolgozás után a `processed/` és `archive/` alatti fájlok UTC timestamp postfixet kapnak:

```text
landing/monthly_sales.xlsx
        |
        v
processed/monthly_sales_20260611T091530Z.xlsx
archive/monthly_sales_20260611T091530Z.xlsx
```

Így egy későbbi, azonos nevű feltöltés nem írja felül a korábbi példányt.

---

# Config-alapú feldolgozás

A config tábla neve:

```text
training_config.file_ingestion_config
```

Egy config sor azt írja le, hogy egy adott fájlmintával mit kell csinálni.

Fontos mezők:

```text
file_pattern       milyen fájlnévre illeszkedik a szabály
source_format      CSV vagy XLSX
sheet_name         Excel esetén melyik sheetet kell olvasni
target_dataset     melyik BigQuery datasetbe töltünk
target_table       melyik RAW táblába töltünk
write_disposition  append vagy truncate mód
expected_columns   milyen oszlopokat várunk a forrásban
target_schema      milyen BigQuery sémával jöjjön létre a cél tábla
```

Példa:

```text
landing/monthly_sales.xlsx
```

Erre három config sor illeszkedik:

```text
Sales sheet       -> janos_raw.sales
Dealers sheet     -> janos_raw.dealer_master
MLI Mapping sheet -> janos_raw.mli_mapping
```

Ezért egyetlen Excel fájlból három BigQuery RAW tábla is betölthető.

---

# RAW tábla létrehozása

A RAW táblákat az importer hozza létre, ha még nem léteznek.

Ehhez a config tábla `target_schema` mezőjét használja:

```sql
[
  STRUCT("dealer_code" AS column_name, "STRING" AS data_type, "NULLABLE" AS mode),
  STRUCT("market" AS column_name, "STRING" AS data_type, "NULLABLE" AS mode)
]
```

A tréningben a RAW üzleti oszlopokat szándékosan `STRING` típusként töltjük be. A típuskonverzió és tisztítás később a BigQuery/Dataform rétegek feladata.

Az importer technikai oszlopokat is hozzáad:

```text
_source_bucket
_source_object
_ingestion_config_id
_ingested_at_utc
```

Ezek segítenek visszakeresni, hogy egy RAW rekord melyik fájlból és melyik config szabály alapján érkezett.

---

# Pub/Sub üzenet

A Cloud Run service Pub/Sub push üzenetet kap.

A Pub/Sub üzenet `message.data` mezője base64-kódolt Cloud Storage object JSON.

Példa dekódolt tartalom:

```json
{
  "bucket": "training-jani",
  "name": "landing/monthly_sales.xlsx",
  "generation": "1781164833074224"
}
```

Az importer ebből olvassa ki:

```text
bucket_name
object_name
object_generation
```

Ezután az `object_name` értékét összeveti a config tábla `file_pattern` mezőivel.

---

# Idempotencia

Pub/Sub esetén fontos szabály:

> Pub/Sub at-least-once delivery modellt használ.

Ez azt jelenti, hogy ugyanaz az üzenet ritka esetben többször is megérkezhet.

Ezért az importer több védelmet is használ:

- a run log alapján ellenőrzi, hogy ugyanaz az objektumgeneráció sikeresen feldolgozódott-e már,
- determinisztikus BigQuery load job ID-t használ,
- a nem `landing/` alatti objektumokat ignorálja,
- a `.keep` placeholder fájlokat ignorálja,
- ha a forrásfájl már eltűnt, `SOURCE_MISSING` státusszal 200-as választ ad.

Ez különösen fontos `WRITE_APPEND` betöltéseknél, mert ott egy duplikált futás duplikált rekordokat okozhatna.

---

# Run log

A futások eredménye a következő táblába kerül:

```text
training_config.file_ingestion_run_log
```

Tipikus státuszok:

```text
SUCCESS
SUCCESS_MOVE_FAILED
UNKNOWN_CONFIG
SOURCE_MISSING
FAILED
```

A run log célja, hogy oktatás és hibakeresés közben látható legyen:

- melyik fájl indította a futást,
- melyik config sorok illeszkedtek,
- melyik táblákba történt betöltés,
- mi lett a feldolgozás eredménye.

---

# Mintafájlok

A `samples/` mappa tartalma:

```text
sales_data.csv
dealer_master.csv
monthly_sales.xlsx
```

A `monthly_sales.xlsx` három sheetet tartalmaz:

```text
Sales
Dealers
MLI Mapping
```

Ezek a minták elegendők a CSV és Excel alapú betöltés bemutatásához.
