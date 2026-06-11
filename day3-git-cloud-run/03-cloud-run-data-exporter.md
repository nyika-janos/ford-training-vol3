# 03 - Cloud Run Data Exporter

## Cél

Ebben a gyakorlatban egy kézzel indítható Data Exporter service-t építünk Cloud Runon.

A cél az, hogy megértsük:

- hogyan lehet egy Cloud Run service-t HTTP kéréssel elindítani,
- hogyan olvas a service BigQuery GOLD táblából,
- hogyan készít Excel fájlt Pythonból,
- hogyan tölti fel az eredményt Cloud Storage-ba,
- hogyan készítünk egyszerű run logot,
- hogyan készítjük elő ugyanazt a megoldást későbbi Airflow ütemezésre.

---

# Architektúra

```text
Manual curl / later Airflow DAG
      |
      | HTTP POST
      v
Cloud Run
data-exporter
      |
      | query
      v
BigQuery GOLD
janos_gold.sales_gold
      |
      | Excel
      v
Cloud Storage bucket
export/
```

Most kézzel indítjuk az exportot. A negyedik napon az Airflow gyakorlatban ugyanez az endpoint hívható ütemezetten, vagy egy GOLD frissítés után.

---

# 1. Lépjünk a service mappájába

Cloud Shellben:

```bash
cd ~/ford-training-vol3/day3-git-cloud-run/materials/data-exporter
```

Ez a mappa tartalmazza a Cloud Run service kódját:

```text
main.py
requirements.txt
Dockerfile
sql/
```

---

# 2. Állítsuk be a változókat

```bash
export PROJECT_ID=ford-training-430008
export REGION=europe-west4
export SERVICE_NAME=data-exporter
export CONFIG_DATASET=training_config
export GOLD_DATASET=janos_gold
export GOLD_TABLE=sales_gold
export BUCKET_NAME=training-jani
```

Mit jelentenek?

```text
PROJECT_ID          GCP projekt
REGION              Cloud Run régió
SERVICE_NAME        Cloud Run service neve
CONFIG_DATASET      BigQuery dataset a log táblának
GOLD_DATASET        BigQuery GOLD dataset
GOLD_TABLE          BigQuery GOLD tábla
BUCKET_NAME         Cloud Storage bucket, ahová az export kerül
```

Fontos: ha a saját Dataform user változód nem `janos`, akkor a GOLD dataset neve is más lesz, például:

```bash
export GOLD_DATASET=anna_gold
```

---

# 3. Engedélyezzük a szükséges API-kat

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com
```

Miért kell?

Cloud Run, Cloud Build, Cloud Storage és BigQuery szolgáltatásokat használunk. Ezeknek az API-knak aktívnak kell lenniük a projektben.

---

# 4. Hozzuk létre az export run log táblát

```bash
bq query --use_legacy_sql=false < sql/01_create_export_log_table.sql
```

Ez a következő táblát hozza létre:

```text
training_config.data_export_run_log
```

Itt fogjuk látni, hogy mikor futott export, melyik táblából dolgozott, hová készült az Excel és hány sort tartalmazott.

---

# 5. Hozzuk létre az export foldert a bucketben

```bash
touch .keep
gsutil cp .keep gs://$BUCKET_NAME/export/.keep
```

Miért kell a `.keep`?

Cloud Storage-ban nincs valódi folder. A Console a fájlnevek prefixei alapján mutat mappaszerű nézetet. A `.keep` egy üres placeholder fájl, hogy az üres `export/` folder is látszódjon.

---

# 6. Deployoljuk a Cloud Run service-t

```bash
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --set-env-vars PROJECT_ID=$PROJECT_ID,CONFIG_DATASET=$CONFIG_DATASET,RUN_LOG_TABLE=data_export_run_log,GOLD_DATASET=$GOLD_DATASET,GOLD_TABLE=$GOLD_TABLE,BUCKET_NAME=$BUCKET_NAME,EXPORT_PREFIX=export/ \
  --allow-unauthenticated
```

Mit csinál ez?

- Cloud Build konténer image-et készít a mappából.
- A Dockerfile alapján összerakja a Python service-t.
- Létrehozza vagy frissíti a Cloud Run service-t.
- Beállítja a környezeti változókat.

Demo célra `--allow-unauthenticated` szerepel. Éles környezetben Cloud Run IAM-et, külön service accountot és Airflow-ból autentikált hívást használnánk.

---

# 7. Mentsük el a Cloud Run URL-t

```bash
export SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format='value(status.url)')

echo $SERVICE_URL
```

Ezt az URL-t fogjuk kézzel meghívni.

---

# 8. Indítsunk egy teljes GOLD exportot

```bash
curl -X POST "$SERVICE_URL" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Várható válasz:

```json
{
  "status": "success",
  "source_table": "ford-training-430008.janos_gold.sales_gold",
  "row_count": 150,
  "export_uri": "gs://training-jani/export/sales_gold_20260611T091530Z.xlsx",
  "run_log_table": "ford-training-430008.training_config.data_export_run_log",
  "run_log_written": true
}
```

A pontos `row_count` és fájlnév eltérhet.

---

# 9. Indítsunk szűrt exportot

Példa egy market exportjára:

```bash
curl -X POST "$SERVICE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "requested_by": "manual-test",
    "export_name": "sales_gold_hu.xlsx",
    "market": "HU"
  }'
```

Példa több szűrővel:

```bash
curl -X POST "$SERVICE_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "export_name": "sales_gold_passenger_crossover.xlsx",
    "market": ["HU", "CZ"],
    "segment": ["Passenger Car", "Crossover"]
  }'
```

A service jelenleg három biztonságos, paraméterezett szűrőt támogat:

```text
market
segment
model
```

Azért nem adunk át tetszőleges SQL `WHERE` feltételt, mert Airflow-ból és kézi hívásból is könnyebb kontrollálni a paraméterezett kéréseket.

---

# 10. Nézzük meg az exportált fájlt

```bash
gsutil ls gs://$BUCKET_NAME/export/
```

Letöltés teszthez:

```bash
gsutil cp gs://$BUCKET_NAME/export/sales_gold_hu.xlsx .
```

Az Excel két sheetet tartalmaz:

```text
sales_gold
export_info
```

A `sales_gold` sheet az üzleti aggregált adatokat tartalmazza.

Az `export_info` sheet megmutatja:

```text
run_id
source_table
exported_at_utc
row_count
filters
```

---

# 11. Nézzük meg a run logot

Fontos: ez nem Dataform run log. Ebbe a táblába csak a `data-exporter` Cloud Run service ír, tehát akkor jelenik meg benne sor, ha a fenti `curl -X POST "$SERVICE_URL"` hívás lefutott.

BigQuery-ben:

```sql
SELECT
  started_at,
  status,
  source_table,
  bucket_name,
  object_name,
  row_count,
  filters,
  requested_by,
  message
FROM `ford-training-430008.training_config.data_export_run_log`
ORDER BY started_at DESC;
```

Itt látszik:

- mikor futott az export,
- melyik GOLD táblából dolgozott,
- hová ment az Excel fájl,
- hány sor került bele,
- milyen szűrőkkel indult.

Ha az Excel fájl létrejött, de ez a tábla üres marad, nézzük meg a `curl` választ és a Cloud Run logokat. A service sikeres logírás esetén `run_log_written: true` mezőt ad vissza.

---

# 12. Cloud Run logok

```bash
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --limit 100
```

Ez akkor hasznos, ha látni szeretnénk:

- megérkezett-e a HTTP kérés,
- volt-e Python hiba,
- volt-e BigQuery vagy Storage jogosultsági hiba,
- milyen választ adott a service.

---

# 13. Hogyan kapcsolódik majd Airflow-hoz?

A service már most orchestration-barát:

```text
Airflow DAG task
      |
      | HTTP POST
      v
Cloud Run data-exporter
      |
      | Excel
      v
gs://training-jani/export/
```

Airflow-ból később ugyanilyen JSON body küldhető:

```json
{
  "requested_by": "airflow:sales_gold_export",
  "export_name": "sales_gold_daily_{{ ds_nodash }}.xlsx"
}
```

Ha a GOLD réteg frissítése is Airflow-ból indul, akkor a DAG sorrendje egyszerűen ez lehet:

```text
1. Dataform / BigQuery GOLD frissítés
2. Cloud Run data-exporter meghívás
3. opcionális ellenőrzés a data_export_run_log alapján
```

---

# 14. Mit tanultunk?

Ebben a gyakorlatban egy klasszikus riport exportot valósítottunk meg cloud-native módon.

```text
BigQuery GOLD
    ↓
Cloud Run
    ↓
Excel
    ↓
Cloud Storage export/
```

A fontos tervezési pontok:

- a service kézzel és orchestrationből is indítható,
- a BigQuery lekérdezés paraméterezett,
- az Excel export tartalmaz üzleti adatot és technikai metadata sheetet,
- az export eredménye bucketben auditálható,
- a run log megmutatja, mi történt egy futás során,
- a későbbi Airflow DAG-nak nem kell ismernie a Python export logikát, csak az endpointot kell meghívnia.
