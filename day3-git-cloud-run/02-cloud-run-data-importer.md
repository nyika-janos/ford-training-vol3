# 02 - Cloud Run Data Importer

## Cél

Ebben a gyakorlatban egy event-driven Data Importer service-t építünk Cloud Runon.

A cél az, hogy megértsük:

- hogyan indít el egy Cloud Storage fájlfeltöltés egy Pub/Sub üzenetet,
- hogyan hívja meg a Pub/Sub a Cloud Run service-t,
- hogyan dolgozik a Cloud Run Python kódja,
- hogyan vezérli a feldolgozást egy BigQuery config tábla,
- hogyan kerülnek az adatok BigQuery RAW táblákba,
- miért fontos az idempotencia.

---

# Architektúra

```text
Excel / CSV file
      |
      | upload
      v
Cloud Storage bucket
landing/
      |
      | notification: OBJECT_FINALIZE, prefix: landing/
      v
Pub/Sub topic
file-upload-topic
      |
      | push subscription
      v
Cloud Run
data-importer
      |
      | lookup
      v
BigQuery config
training_config.file_ingestion_config
      |
      | load
      v
BigQuery RAW
janos_raw.sales
janos_raw.dealer_master
janos_raw.mli_mapping
```

---

# 1. Lépjünk a service mappájába

Cloud Shellben:

```bash
cd ~/ford-training-vol3/day3-git-cloud-run/materials/data-importer
```

Ez a mappa tartalmazza a Cloud Run service kódját:

```text
main.py
requirements.txt
Dockerfile
sql/
samples/
```

---

# 2. Állítsuk be a változókat

```bash
export PROJECT_ID=ford-training-430008
export REGION=europe-west4
export SERVICE_NAME=data-importer
export CONFIG_DATASET=training_config
export RAW_DATASET=janos_raw
export BUCKET_NAME=training-jani
export TOPIC_NAME=file-upload-topic
export SUBSCRIPTION_NAME=file-upload-to-importer
```

Mit jelentenek?

```text
PROJECT_ID          GCP projekt
REGION              Cloud Run régió
SERVICE_NAME        Cloud Run service neve
CONFIG_DATASET      BigQuery dataset a config és log tábláknak
RAW_DATASET         BigQuery RAW dataset
BUCKET_NAME         Cloud Storage bucket
TOPIC_NAME          Pub/Sub topic
SUBSCRIPTION_NAME   Pub/Sub push subscription
```

---

# 3. Engedélyezzük a szükséges API-kat

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  pubsub.googleapis.com \
  storage.googleapis.com \
  bigquery.googleapis.com
```

Miért kell?

Cloud Run, Cloud Build, Pub/Sub, Cloud Storage és BigQuery szolgáltatásokat fogunk használni. Ezeknek az API-knak aktívnak kell lenniük a projektben.

---

# 4. Hozzuk létre a BigQuery dataseteket

Config dataset:

```bash
bq --location=europe-west4 mk --dataset $PROJECT_ID:$CONFIG_DATASET
```

RAW dataset:

```bash
bq --location=europe-west4 mk --dataset $PROJECT_ID:$RAW_DATASET
```

Ha már léteznek, a parancs hibát adhat. Ez nem gond, ilyenkor tovább lehet menni.

---

# 5. Hozzuk létre a config és run log táblákat

```bash
bq query --use_legacy_sql=false < sql/01_create_config_tables.sql
```

Ez két táblát hoz létre:

```text
training_config.file_ingestion_config
training_config.file_ingestion_run_log
```

A `file_ingestion_config` mondja meg, mit kell feldolgozni.

A `file_ingestion_run_log` megmutatja, mi történt egy futás során.

---

# 6. Töltsük be a sample config sorokat

```bash
bq query --use_legacy_sql=false < sql/02_sample_configs.sql
```

A sample config 5 szabályt tartalmaz:

```text
sales_data.csv        -> janos_raw.sales
dealer_master.csv     -> janos_raw.dealer_master
monthly_sales.xlsx / Sales       -> janos_raw.sales
monthly_sales.xlsx / Dealers     -> janos_raw.dealer_master
monthly_sales.xlsx / MLI Mapping -> janos_raw.mli_mapping
```

Fontos: ha nem `janos_raw` a saját RAW dataseted, akkor a `02_sample_configs.sql` fájlban cseréld át a dataset nevét futtatás előtt.

---

# 7. Hozzuk létre a Pub/Sub topicot

```bash
gcloud pubsub topics create $TOPIC_NAME
```

Miért kell?

A Cloud Storage notification ide küldi az üzenetet, amikor új fájl érkezik a `landing/` folderbe.

---

# 8. Deployoljuk a Cloud Run service-t

```bash
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --set-env-vars PROJECT_ID=$PROJECT_ID,CONFIG_DATASET=$CONFIG_DATASET,CONFIG_TABLE=file_ingestion_config,RUN_LOG_TABLE=file_ingestion_run_log,LANDING_PREFIX=landing/,PROCESSED_PREFIX=processed/,ARCHIVE_PREFIX=archive/,ERROR_PREFIX=error/ \
  --allow-unauthenticated
```

Mit csinál ez?

- Cloud Build konténer image-et készít a mappából.
- A Dockerfile alapján összerakja a Python service-t.
- Létrehozza vagy frissíti a Cloud Run service-t.
- Beállítja a környezeti változókat.

Demo célra `--allow-unauthenticated` szerepel. Éles környezetben Pub/Sub OIDC autentikációt és külön service accountot használnánk.

---

# 9. Mentsük el a Cloud Run URL-t

```bash
export SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format='value(status.url)')

echo $SERVICE_URL
```

Erre az URL-re fog pusholni a Pub/Sub subscription.

---

# 10. Hozzuk létre a Pub/Sub push subscriptiont

```bash
gcloud pubsub subscriptions create $SUBSCRIPTION_NAME \
  --topic $TOPIC_NAME \
  --push-endpoint $SERVICE_URL \
  --ack-deadline=120
```

Miért fontos az `ack-deadline=120`?

A Pub/Sub alapértelmezett ack deadline-ja gyakran 10 másodperc. Ha az import tovább tart, a Pub/Sub ugyanazt az üzenetet újraküldheti még az első futás közben.

A 120 másodperc kényelmesebb a demóhoz.

---

# 11. Hozzuk létre a bucket folder struktúrát

```bash
touch .keep

gsutil cp .keep gs://$BUCKET_NAME/landing/.keep
gsutil cp .keep gs://$BUCKET_NAME/processed/.keep
gsutil cp .keep gs://$BUCKET_NAME/archive/.keep
gsutil cp .keep gs://$BUCKET_NAME/error/.keep
```

Miért kell a `.keep`?

Cloud Storage-ban nincs valódi folder. A Console a fájlnevek prefixei alapján mutat mappaszerű nézetet. A `.keep` egy üres placeholder fájl, hogy az üres folder is látszódjon.

---

# 12. Hozzuk létre a Cloud Storage notificationt

```bash
gsutil notification create \
  -t $TOPIC_NAME \
  -f json \
  -e OBJECT_FINALIZE \
  -p landing/ \
  gs://$BUCKET_NAME
```

Miért fontos a `-p landing/`?

Így csak a `landing/` alá érkező új objektumokról megy Pub/Sub üzenet.

Ha nincs prefix, akkor a `processed/`, `archive/` és `error/` alatti fájlmozgatások is új üzeneteket generálnának.

---

# 13. Teszteljük CSV fájllal

```bash
gsutil cp samples/sales_data.csv gs://$BUCKET_NAME/landing/sales_data.csv
```

Várható eredmény:

```text
janos_raw.sales
```

Töltsük fel a dealer mastert is:

```bash
gsutil cp samples/dealer_master.csv gs://$BUCKET_NAME/landing/dealer_master.csv
```

Várható eredmény:

```text
janos_raw.dealer_master
```

---

# 14. Teszteljük Excel fájllal

```bash
gsutil cp samples/monthly_sales.xlsx gs://$BUCKET_NAME/landing/monthly_sales.xlsx
```

Az Excel három sheetet tartalmaz:

```text
Sales
Dealers
MLI Mapping
```

Várható eredmény:

```text
janos_raw.sales
janos_raw.dealer_master
janos_raw.mli_mapping
```

---

# 15. Nézzük meg a run logot

BigQuery-ben:

```sql
SELECT
  started_at,
  object_name,
  object_generation,
  status,
  config_ids,
  target_tables,
  message
FROM `ford-training-430008.training_config.file_ingestion_run_log`
ORDER BY started_at DESC;
```

Itt látszik:

- melyik fájl indította a futást,
- melyik config sorok illeszkedtek,
- melyik táblákba töltött,
- sikeres volt-e a feldolgozás.

---

# 16. Nézzük meg a bucket eredményt

```bash
gsutil ls gs://$BUCKET_NAME/landing/
gsutil ls gs://$BUCKET_NAME/processed/
gsutil ls gs://$BUCKET_NAME/archive/
gsutil ls gs://$BUCKET_NAME/error/
```

Sikeres feldolgozás után az eredeti fájl eltűnik a `landing/` alól, és timestampelt névvel megjelenik:

```text
processed/
archive/
```

---

# 17. Cloud Run logok

```bash
gcloud run services logs read $SERVICE_NAME \
  --region $REGION \
  --limit 100
```

Ez akkor hasznos, ha látni szeretnénk:

- megérkezett-e a Pub/Sub push,
- volt-e Python hiba,
- volt-e BigQuery vagy Storage hiba,
- hogyan viselkedett a retry/idempotencia logika.

---

# 18. Mit tanultunk?

Ebben a gyakorlatban egy klasszikus Alteryx jellegű fájlbetöltést cloud-native módon valósítottunk meg.

```text
File upload
    ↓
Cloud Storage
    ↓
Pub/Sub
    ↓
Cloud Run
    ↓
BigQuery RAW
```

A fontos tervezési pontok:

- a feldolgozás event-driven,
- a Python kód konfigurációból dolgozik,
- a RAW táblák sémája configból jön,
- a run log auditálhatóvá teszi a folyamatot,
- a Pub/Sub miatt idempotens feldolgozás kell,
- a `landing/` prefix segít elkerülni a felesleges üzeneteket.
