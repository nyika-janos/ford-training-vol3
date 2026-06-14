# Ford GCP Training – 3. kötet

<p align="center">
  <img src="other/ford-training-vol3_architecture.png" alt="A Ford training 3. kötetének target architecture diagramja" width="100%">
</p>

## Áttekintés

Ez a repository tartalmazza a Ford data team harmadik GCP trainingjén használt hands-on gyakorlatokat.

A training elsődleges célja annak bemutatása, hogyan migrálhatók a meglévő Alteryx workflow-k modern Google Cloud Platform architecture-re native GCP services használatával.

A training olyan analyst és data professional résztvevőknek készült, akik kevés cloud engineering tapasztalattal rendelkeznek. A gyakorlatok az architecture, az egyes componentek felelősségi köre és a közöttük lévő interakciók megértésére összpontosítanak.

A példák olyan valós workflow-kon alapulnak, amelyek jelenleg az alábbiakat használják:

- Excel-fájlok
- SharePoint
- BigQuery
- Alteryx

A target architecture az alábbiakat használja:

- Cloud Storage
- Pub/Sub
- BigQuery
- Dataform
- Cloud Run
- Cloud Scheduler
- BigQuery Data Transfer Service
- Cloud Composer (Airflow)

---

# A training célja

A training végére a résztvevők megértik, hogyan implementálható egy tipikus Alteryx workflow Google Cloud services használatával.

A végleges architecture az alábbihoz lesz hasonló:

```text
SharePoint / Excel / CSV / XML / MS Access / BigQuery sources
                     ↓
              Ingestion services
        Cloud Storage, Cloud Run, DTS
                     ↓
                  BigQuery RAW
                     ↓
                  Dataform
                     ↓
          STAGE → INTERMEDIATE → GOLD
                     ↓
          Power BI report / Excel export
```

A teljes folyamat orchestrationjét a Cloud Composer (Airflow) végzi.

A diagram high-level nézetben három ingestion patternt mutat be:

- A SharePoint fájlokat a Microsoft Graph API-n keresztül érjük el, majd importáljuk a Cloud Storage-ba.
- A Cloud Storage-ba érkező fájlok Pub/Sub notification eventeket válthatnak ki, amelyek elindítják a Cloud Run-alapú import logicot.
- A meglévő BigQuery és MS Access source-ok a BigQuery Data Transfer Service, a Cloud Scheduler és a Cloud Run jobs segítségével tölthetők be a RAW layerbe.

A BigQuery-n belül a RAW-tól a STAGE, INTERMEDIATE és GOLD datasetekig tartó transformation flow a Dataform felelőssége. A GOLD layert ezután Power BI reportok használják fel, vagy a Cloud Run visszaexportálja Excelbe.

---

# A training felépítése

A training négy félnapos sessionből áll.

## 1. nap

### Cloud Storage & Pub/Sub

Témakörök:

- Cloud Storage
- Landing Zone design
- Bucket structure
- Event-driven architecture
- Pub/Sub fundamentals

Hands-on gyakorlatok:

- Személyes bucket létrehozása
- Enterprise folder structure létrehozása
- Excel fájlok feltöltése
- Pub/Sub topicok létrehozása
- Subscriptionök létrehozása
- Cloud Storage notificationök konfigurálása
- Pub/Sub eventek generálása és vizsgálata

Végeredmény:

```text
Excel
   ↓
Cloud Storage
   ↓
Pub/Sub
   ↓
Message
```

---

## 2. nap

### BigQuery & Dataform

Témakörök:

- Data warehouse fundamentals
- Raw / Staging / Intermediate / Gold layers
- BigQuery datasetek
- Table-ök és view-k
- Dataform
- Dataform vs dbt

Hands-on gyakorlatok:

- Datasetek létrehozása
- External table-ök létrehozása
- Native table-ök létrehozása
- View-k létrehozása
- Dataform modellek építése
- Transformationök létrehozása
- Gold table létrehozása

Végeredmény:

```text
Excel
   ↓
Cloud Storage
   ↓
BigQuery Raw
   ↓
Dataform
   ↓
Gold Table
```

---

## 3. nap

### Cloud Run

Témakörök:

- Serverless compute
- Cloud Run Services
- Cloud Run Jobs
- Event-driven processing
- Python-alapú integrationök
- Manuális, HTTP-triggered service-ek a későbbi orchestration előkészítéséhez

Hands-on gyakorlatok:

- A Git és a Cloud Shell használata a training repositoryhoz
- Cloud Run service deployolása
- Pub/Sub eventek összekapcsolása a Cloud Runnal
- CSV- és Excel-fájlok beolvasása a Cloud Storage-ból
- Landing Zone fájlok betöltése BigQuery RAW table-ökbe
- BigQuery GOLD adatok exportálása Excelbe
- Importer és exporter run logok írása

Végeredmény:

```text
Excel
   ↓
Cloud Storage
   ↓
Pub/Sub
   ↓
Cloud Run
   ↓
BigQuery
   ↓
Dataform GOLD
   ↓
Cloud Run
   ↓
Excel export
```

A 3. nap két Cloud Run service patternt tartalmaz:

- `data-importer`: event-driven service, amelyet a Pub/Sub indít el, amikor fájl érkezik a bucket `landing/` folderébe.
- `data-exporter`: HTTP-triggered service, amely a BigQuery `sales_gold` adatait egy Excel-fájlba exportálja a bucket `export/` folderében.

A 3. napon az exportert szándékosan manuálisan, `curl` használatával hívjuk meg. Így a service könnyen érthető marad, mielőtt a 4. napon megismerkedünk az Airflow orchestrationnel.

---

## 4. nap

### Cloud Composer (Airflow)

Témakörök:

- Workflow orchestration
- DAGs
- Scheduling
- Monitoring
- Error handling
- Retry stratégiák

Hands-on gyakorlatok:

- Airflow DAG-ok létrehozása
- Cloud Run triggerelése
- Dataform triggerelése
- Execution monitorozása
- End-to-end pipeline építése

Végeredmény:

```text
Excel
   ↓
Cloud Storage
   ↓
Pub/Sub
   ↓
Cloud Run
   ↓
BigQuery
   ↓
Dataform
   ↓
Gold Layer
   ↓
Export
```

A 4. nap összekapcsolja az első három nap elemeit. Az Airflow segítségével koordináljuk az operationök sorrendjét: frissítjük a BigQuery/Dataform layereket, meghívjuk a Cloud Run service-eket, például a data exportert, monitorozzuk az eredményeket, valamint egyetlen orchestration layerben tesszük láthatóvá a retry/error handling működését.

---

# A repository felépítése

```text
ford-training-vol3
│
├── README.md
│
├── day1-storage-pubsub
│   ├── 01-create-bucket.md
│   ├── 02-create-folder-structure.md
│   ├── 03-upload-excel.md
│   ├── 04-create-topic.md
│   ├── 05-create-subscription.md
│   └── 06-create-notification-and-test.md
│
├── day2-bigquery-dataform
│   ├── 01-create-datasets.md
│   ├── 02-load-raw-tables.md
│   ├── 03-explore-data.md
│   ├── 04-create-dataform-repository.md
│   ├── 05-create-stage-models.md
│   ├── 06-create-intermediate-model.md
│   ├── 07-create-gold-model.md
│   ├── 08-run-dataform.md
│   ├── materials
│   │   ├── dealer_master.csv
│   │   ├── dataform
│   │   ├── mli_mapping.csv
│   │   └── sales_data.csv
│   └── theory
│       ├── 01-bq-deep-dive.md
│       ├── 02-dataform-deep-dive.md
│       └── 03-dataform-repo-workspace.md
│
├── day3-git-cloud-run
│   ├── 01-git-alapok.md
│   ├── 02-cloud-run-data-importer.md
│   ├── 03-cloud-run-data-exporter.md
│   └── materials
│       ├── data-importer
│       │   ├── Dockerfile
│       │   ├── README.md
│       │   ├── main.py
│       │   ├── requirements.txt
│       │   ├── samples
│       │   └── sql
│       └── data-exporter
│           ├── Dockerfile
│           ├── README.md
│           ├── main.py
│           ├── requirements.txt
│           └── sql
│
└── day4-composer
    ├── 01-create-composer-environment.md
    ├── ...
```

---

# Előfeltételek

A résztvevőknek az alábbiakkal kell rendelkezniük:

- Hozzáférés a training GCP projecthez
- Editor jogosultságok
- Google account
- Alapszintű SQL-ismeretek
- Alapszintű Excel-ismeretek

Nem szükséges előzetes tapasztalat az alábbiakkal:

- Cloud Run
- Dataform
- Composer
- Pub/Sub

---

# Training project

Project ID:

```text
ford-training-430008
```

A repository összes gyakorlata azt feltételezi, hogy a résztvevők ebben a projectben dolgoznak.

---

# Fontos megjegyzés

A gyakorlatok szándékosan az architecture megértésére, nem pedig production-ready solutionök építésére összpontosítanak.

Számos enterprise témakört, például az alábbiakat:

- CI/CD
- Terraform
- Secret Manager
- IAM best practices
- Monitoring
- Cost optimization
- Security hardening

leegyszerűsítünk, hogy a fókusz az Alteryxről GCP-re történő migration folyamatán maradjon.

A cél annak megértése:

- Melyik GCP component milyen problémát old meg
- Hogyan működnek együtt a componentek
- Hogyan képezhető le egy Alteryx workflow cloud-native architecture-re

---

# Tanulási eredmények

A training elvégzése után a résztvevők képesek lesznek:

- Megérteni a target GCP architecture-t
- Fájlokat ingestálni a Cloud Storage-ba
- Eventeket feldolgozni a Pub/Sub segítségével
- Adatokat tárolni és transformálni a BigQuery-ben
- Dataform pipeline-okat építeni
- Python workloadokat futtatni a Cloud Runban
- Workflow-kat orchestrálni az Airflow segítségével
- Megérteni, hogyan migrálhatók a meglévő Alteryx workflow-k GCP-re

---

# Architecture összefoglaló

```text
SharePoint / Excel / CSV / XML / MS Access / BigQuery
                    ↓
          Cloud Storage / Cloud Run / DTS
                    ↓
                BigQuery RAW
                    ↓
                 Dataform
                    ↓
       STAGE → INTERMEDIATE → GOLD
                    ↓
          Power BI / Excel Export

Cloud Composer (Airflow)
      orchestrálja
   a teljes flow-t
```
