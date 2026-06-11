# Data Exporter Cloud Run

Ez a mappa egy kézzel indítható Cloud Run exportert tartalmaz.

A service célja, hogy a BigQuery GOLD réteg `sales_gold` táblájából Excel fájlt készítsen, majd feltöltse a training bucket `export/` folderébe.

---

# Magas szintű működés

```text
User / Airflow later
        |
        | HTTP POST
        v
Cloud Run Data Exporter
        |
        | query
        v
BigQuery GOLD
janos_gold.sales_gold
        |
        | Excel file
        v
Cloud Storage bucket
export/
```

Most kézzel hívjuk meg `curl` paranccsal. A negyedik napi Airflow gyakorlatban ugyanez az endpoint hívható egy DAG taskból.

---

# Endpoint

```text
POST /
GET  /health
```

Minimális kérés:

```json
{}
```

Opcionális kérés:

```json
{
  "requested_by": "manual-training-test",
  "export_name": "sales_gold_hu.xlsx",
  "market": "HU"
}
```

Több értékes szűrés:

```json
{
  "export_name": "sales_gold_passenger_crossover.xlsx",
  "market": ["HU", "CZ"],
  "segment": ["Passenger Car", "Crossover"]
}
```

Támogatott szűrők:

```text
market
segment
model
```

Sikeres válasz példa:

```json
{
  "status": "success",
  "run_id": "18aca2b6-8167-4ee7-88b4-065e5063d4fa",
  "source_table": "ford-training-430008.janos_gold.sales_gold",
  "row_count": 10,
  "export_uri": "gs://training-jani/export/sales_gold_passenger_crossover.xlsx",
  "run_log_table": "ford-training-430008.training_config.data_export_run_log",
  "run_log_written": true
}
```

A `run_log_written: true` azt jelzi, hogy az export eredménye bekerült a BigQuery run log táblába is.

---

# Környezeti változók

```text
PROJECT_ID          GCP projekt
GOLD_DATASET        BigQuery GOLD dataset, alapértelmezés: janos_gold
GOLD_TABLE          BigQuery GOLD tábla, alapértelmezés: sales_gold
BUCKET_NAME         cél Cloud Storage bucket
EXPORT_PREFIX       cél prefix, alapértelmezés: export/
CONFIG_DATASET      log dataset, alapértelmezés: training_config
RUN_LOG_TABLE       log tábla, alapértelmezés: data_export_run_log
```

---

# Excel tartalom

Az exportált fájl két sheetet tartalmaz:

```text
sales_gold
export_info
```

A `sales_gold` sheet a BigQuery tábla üzleti adatait tartalmazza.

Az `export_info` sheet technikai metadata:

```text
run_id
source_table
exported_at_utc
row_count
filters
```

---

# Run log

A futások eredménye a következő táblába kerül:

```text
training_config.data_export_run_log
```

Fontos: ez nem Dataform run log. A tábla csak akkor kap sort, amikor a `data-exporter` Cloud Run endpointot meghívjuk.

A `filters` oszlop BigQuery `JSON` típusú mezőként tárolja, hogy milyen `market`, `segment` vagy `model` szűrőkkel indult a futás.

Tipikus státuszok:

```text
SUCCESS
FAILED
```

Ez segít visszakeresni:

- mikor futott export,
- melyik GOLD táblából dolgozott,
- hová töltötte az Excel fájlt,
- hány sort exportált,
- milyen szűrők voltak aktívak.
