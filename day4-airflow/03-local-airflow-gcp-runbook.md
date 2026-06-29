# 03 - Lokális Airflow GCP DAG-ok futtatása

Ez a runbook a 02-es anyag gyakorlati párja: hogyan másoljuk be a DAG-okat, milyen csomagok kellenek, hogyan állítjuk be a GCP autentikációt, milyen Airflow Variable-öket importálunk, és milyen sorrendben érdemes futtatni a DAG-okat.

Kapcsolódó koncepcionális leírás: [02-local-airflow-gcp-pipeline.md](02-local-airflow-gcp-pipeline.md)

---

## 1. DAG fájlok

A repositoryban a DAG-ok itt vannak:

```text
day4-airflow/materials/dags/sales_export_dag.py
day4-airflow/materials/dags/sales_dataform_export_dag.py
day4-airflow/materials/dags/parallel_market_exports_dag.py
day4-airflow/materials/dags/branching_market_export_dag.py
day4-airflow/materials/dags/pipeline_with_notifications_dag.py
day4-airflow/materials/dags/bigquery_operator_showcase_dag.py
```

Másold őket a lokális Airflow projekt `dags` mappájába.

Ha az első gyakorlat szerint dolgoztál:

```bash
cp ~/ford-training-vol3/day4-airflow/materials/dags/sales_export_dag.py ~/gcp-training-airflow/dags/
cp ~/ford-training-vol3/day4-airflow/materials/dags/sales_dataform_export_dag.py ~/gcp-training-airflow/dags/
cp ~/ford-training-vol3/day4-airflow/materials/dags/parallel_market_exports_dag.py ~/gcp-training-airflow/dags/
cp ~/ford-training-vol3/day4-airflow/materials/dags/branching_market_export_dag.py ~/gcp-training-airflow/dags/
cp ~/ford-training-vol3/day4-airflow/materials/dags/pipeline_with_notifications_dag.py ~/gcp-training-airflow/dags/
cp ~/ford-training-vol3/day4-airflow/materials/dags/bigquery_operator_showcase_dag.py ~/gcp-training-airflow/dags/
```

Windows PowerShell példa:

```powershell
copy .\day4-airflow\materials\dags\sales_export_dag.py $HOME\gcp-training-airflow\dags\
copy .\day4-airflow\materials\dags\sales_dataform_export_dag.py $HOME\gcp-training-airflow\dags\
copy .\day4-airflow\materials\dags\parallel_market_exports_dag.py $HOME\gcp-training-airflow\dags\
copy .\day4-airflow\materials\dags\branching_market_export_dag.py $HOME\gcp-training-airflow\dags\
copy .\day4-airflow\materials\dags\pipeline_with_notifications_dag.py $HOME\gcp-training-airflow\dags\
copy .\day4-airflow\materials\dags\bigquery_operator_showcase_dag.py $HOME\gcp-training-airflow\dags\
```

---

## 2. Szükséges Python csomagok

A DAG-ok Pythonból hívják a GCP API-kat, ezért az Airflow konténerekben szükség van néhány csomagra.

A lokális Airflow projekt mappájában nyisd meg a `.env` fájlt:

```bash
cd ~/gcp-training-airflow
nano .env
```

Add hozzá:

```text
_PIP_ADDITIONAL_REQUIREMENTS=google-cloud-bigquery google-cloud-storage google-auth requests
```

Ha a `bigquery_operator_showcase_dag` DAG-ot is használni szeretnéd, akkor szükség van a Google Airflow providerre is:

```text
_PIP_ADDITIONAL_REQUIREMENTS=apache-airflow-providers-google google-cloud-bigquery google-cloud-storage google-auth requests
```

Megjegyzés: a provider csomag nagyobb dependency csomagot húzhat be, ezért a fő pipeline DAG-ok nem erre épülnek.

Windows PowerShellben szerkesztheted VS Code-dal is:

```powershell
code .env
```

Megjegyzés: ez tréninghez kényelmes megoldás. Production Airflow környezetben inkább saját Docker image-be tennénk a dependencyket.

---

## 3. Google provider connection

Ez csak a `bigquery_operator_showcase_dag` futtatásához kell.

A BigQuery provider operator nem csak Airflow Variable-öket használ, hanem Airflow Connectiont is. Ezért ha ezt látod:

```text
AirflowNotFoundException: The conn_id `google_cloud_default` isn't defined
```

akkor nem változó hiányzik, hanem a `google_cloud_default` nevű connection.

A lokális Airflow projekt mappájában add hozzá CLI-ból:

```bash
cd ~/gcp-training-airflow

docker compose exec airflow-apiserver airflow connections add google_cloud_default \
  --conn-type google-cloud-platform \
  --conn-extra '{
    "extra__google_cloud_platform__project": "ford-training-430008",
    "extra__google_cloud_platform__scope": "https://www.googleapis.com/auth/cloud-platform"
  }'
```

Ha a compose setupodban nincs `airflow-apiserver` service, próbáld a webserverrel:

```bash
docker compose exec airflow-webserver airflow connections add google_cloud_default \
  --conn-type google-cloud-platform \
  --conn-extra '{
    "extra__google_cloud_platform__project": "ford-training-430008",
    "extra__google_cloud_platform__scope": "https://www.googleapis.com/auth/cloud-platform"
  }'
```

Airflow UI-ból is felvehető:

```text
Admin / Connections / +
Connection Id: google_cloud_default
Connection Type: Google Cloud
Project Id: ford-training-430008
Scope: https://www.googleapis.com/auth/cloud-platform
```

Fontos: a `Keyfile JSON` mezőt hagyd üresen. Az `application_default_credentials.json`, amit a `gcloud auth application-default login` készít, user credential, nem service account key. Ha ezt bemásolod a `Keyfile JSON` mezőbe, ilyen hibát kapsz:

```text
MalformedError: Service account info was not in the expected format, missing fields token_uri, client_email.
```

Ebben a tréning setupban a connection csak azt mondja meg, hogy Google Cloud kapcsolat kell, a tényleges credentialt pedig a következő fejezetben beállított `GOOGLE_APPLICATION_CREDENTIALS` env var adja.

Ha már létrehoztad rossz tartalommal a connectiont, töröld és vedd fel újra:

```bash
docker compose exec airflow-apiserver airflow connections delete google_cloud_default

docker compose exec airflow-apiserver airflow connections add google_cloud_default \
  --conn-type google-cloud-platform \
  --conn-extra '{
    "extra__google_cloud_platform__project": "ford-training-430008",
    "extra__google_cloud_platform__scope": "https://www.googleapis.com/auth/cloud-platform"
  }'
```

Ha más projectben dolgozol, természetesen a saját project id-t használd.

---

## 4. GCP autentikáció lokális Airflowhoz

Lokális Airflow esetén a konténer nem látja automatikusan a géped `gcloud` belépését.

Először készíts Application Default Credentials fájlt.

```bash
gcloud auth application-default login
```

Ez böngészőben bejelentkeztet a Google accountoddal, majd létrehoz egy lokális credentials fájlt.

### macOS / Linux

Másold be a credentials fájlt az Airflow projekt `config` mappájába:

```bash
cp ~/.config/gcloud/application_default_credentials.json \
  ~/gcp-training-airflow/config/application_default_credentials.json
```

### Windows PowerShell

```powershell
copy $env:APPDATA\gcloud\application_default_credentials.json `
  $HOME\gcp-training-airflow\config\application_default_credentials.json
```

Fontos: ezt a fájlt ne commitold Gitbe. Személyes credential.

---

## 5. `docker-compose.yaml` módosítása

Az Airflow konténereknek meg kell mondani, hol találják a credential fájlt.

A lokális Airflow projektben nyisd meg:

```text
docker-compose.yaml
```

Keresd meg az `x-airflow-common` blokk alatt az `environment` részt, és add hozzá:

```yaml
GOOGLE_APPLICATION_CREDENTIALS: /opt/airflow/config/application_default_credentials.json
GOOGLE_CLOUD_PROJECT: ford-training-430008
```

A hivatalos Airflow compose fájlban a `config` mappa általában már mountolva van:

```yaml
- ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config
```

Ha ez megvan, akkor a fenti credentials fájl látszani fog a konténerből.

Indítsd újra az Airflow-t:

```bash
docker compose down
docker compose up -d
```

Az első újraindítás lassabb lehet, mert a Python csomagok települnek.

---

## 6. GCP jogosultságok

Annak a Google accountnak vagy service accountnak, amelyik az Application Default Credentials mögött van, legalább ezekre van szüksége:

| Komponens | Mire kell jogosultság? |
|---|---|
| BigQuery | `sales_gold` tábla olvasása, query job futtatása |
| Cloud Storage | export fájl ellenőrzése az `export/` folderben |
| Dataform | compilation result és workflow invocation létrehozása |
| Cloud Run | csak akkor kell explicit invoker jog, ha az exporter nem unauthenticated |

Demo módban a 3. napi exporter `--allow-unauthenticated` beállítással futott, ezért a Cloud Run híváshoz nem kell külön token.

Ha később authenticated Cloud Run hívást szeretnénk mutatni, akkor:

- az Airflow credential mögötti identity kapjon Cloud Run Invoker jogot,
- a `cloud_run_exporter_authenticated` Airflow Variable értéke legyen `true`,
- lehetőleg service account alapú credentialt használjunk.

---

## 7. Airflow Variables beállítása

A DAG-ok nem hardcode-olják a résztvevő saját neveit és URL-jeit. Ezeket Airflow Variables-ben állítjuk be.

Nyisd meg:

```text
http://localhost:8080
```

Menj ide:

```text
Admin / Variables
```

Hozd létre az alábbi változókat.

Ha nem szeretnéd kézzel felvenni őket, használd az előkészített import fájlt:

```text
day4-airflow/materials/airflow_variables/day4_airflow_variables.json
```

Másold be a lokális Airflow projektbe:

```bash
cp ~/ford-training-vol3/day4-airflow/materials/airflow_variables/day4_airflow_variables.json \
  ~/gcp-training-airflow/config/day4_airflow_variables.json
```

Import CLI-ból:

```bash
docker compose exec airflow-apiserver airflow variables import \
  /opt/airflow/config/day4_airflow_variables.json
```

Ha a compose setupodban nincs `airflow-apiserver` service, próbáld a webserverrel:

```bash
docker compose exec airflow-webserver airflow variables import \
  /opt/airflow/config/day4_airflow_variables.json
```

Import után az alábbi értéket mindenképp ellenőrizd vagy cseréld:

```text
cloud_run_exporter_url
```

Az import fájlban ez szándékosan placeholder:

```text
REPLACE_WITH_DATA_EXPORTER_URL
```

Ezt átírhatod import előtt a JSON fájlban, vagy import után az Airflow UI-ban.

Az exporter URL-t így tudod lekérdezni Cloud Shellben vagy olyan gépen, ahol van `gcloud`:

```bash
gcloud run services describe data-exporter \
  --region europe-west4 \
  --format='value(status.url)'
```

### Közös változók

| Key | Példa value | Megjegyzés |
|---|---|---|
| `project_id` | `ford-training-430008` | GCP project |
| `bucket_name` | `training-jani` | saját training bucket |
| `gold_dataset` | `janos_gold` | saját GOLD dataset |
| `gold_table` | `sales_gold` | GOLD tábla |
| `export_prefix` | `export/` | Cloud Storage export folder |
| `cloud_run_exporter_url` | `https://data-exporter-...run.app` | 3. napi exporter URL |
| `cloud_run_exporter_authenticated` | `false` | demo módban false |

### Dataform változók

Ezek csak a `sales_dataform_export_dag` futtatásához kellenek.

| Key | Példa value | Megjegyzés |
|---|---|---|
| `dataform_location` | `europe-west4` | Dataform repository régió |
| `dataform_repository` | `janos_training_dataform` | saját repository |
| `dataform_service_account` | `dataform-runner@ford-training-430008.iam.gserviceaccount.com` | custom futtató service account |
| `dataform_git_commitish` | `main` | Git branch / commit / tag, amit compile-olunk |
| `dataform_workspace` | `development` | opcionális; ha be van állítva, workspace-ből compile-olunk |
| `dataform_wait_timeout_seconds` | `900` | maximum várakozás |
| `dataform_poll_seconds` | `15` | poll gyakoriság |
| `demo_task_delay_seconds` | `3` | mesterséges várakozás másodpercben a látványosabb demo kedvéért |
| `branching_export_row_threshold` | `100` | ha a GOLD rekordok száma ennél nagyobb, a branching DAG marketenként exportál |
| `gcp_conn_id` | `google_cloud_default` | Airflow Google provider connection id az operatoros példához |
| `bigquery_location` | `europe-west4` | BigQuery job location az operatoros példához |

A 2. napi setupban a repository jellemzően így nézett ki:

```text
<your_name>_training_dataform
```

Példa:

```text
janos_training_dataform
```

Ha `dataform_workspace` be van állítva, akkor a DAG workspace-ből compile-ol. Ez hasznos akkor, ha a Dataform UI-ban korábban a `development` workspace compile/run már működött.

Ha `dataform_workspace` nincs beállítva, akkor a DAG a `dataform_git_commitish` érték alapján, például a GitHub `main` branchből compile-ol.

Ha Git branchből compile-oláskor a Dataform API ezt a hibát adja:

```text
Can't find package.json
```

akkor a Dataform nem ugyanazt a projektgyökeret látja, mint amit a UI-ban használtál. Ilyenkor a tréningen egyszerűbb visszaállni workspace compile-ra:

```text
dataform_workspace = development
```

### Dataform service account megjegyzés

Strict act-as módban a Dataform nem futhat a default Dataform service agenttel.

Ez nem használható workflow futtató service accountként:

```text
service-<PROJECT_NUMBER>@gcp-sa-dataform.iam.gserviceaccount.com
```

Ez a Dataform service agent. A Google dokumentáció szerint strict act-as módban workflow futtatáshoz custom service accountot vagy user credentialt kell használni.

Ebben a tréningben használjunk custom service accountot:

```text
dataform-runner@ford-training-430008.iam.gserviceaccount.com
```

Ezt add meg Airflow Variable-ként:

```text
dataform_service_account
```

Ha még nincs ilyen service account, létrehozható:

```bash
gcloud iam service-accounts create dataform-runner \
  --display-name="Dataform Runner"
```

Példa jogosultságok:

```bash
gcloud projects add-iam-policy-binding ford-training-430008 \
  --member="serviceAccount:dataform-runner@ford-training-430008.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding ford-training-430008 \
  --member="serviceAccount:dataform-runner@ford-training-430008.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

Annak az identitynek, amellyel a lokális Airflow autentikál a GCP felé, jogosultnak kell lennie a repositoryt olvasni és workflow invocationt létrehozni. Ha custom service accountot használsz, akkor a Dataform default service agentnek is tudnia kell azt használni.

Példa Dataform service agent jogosítására:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  dataform-runner@ford-training-430008.iam.gserviceaccount.com \
  --member="serviceAccount:service-227551883136@gcp-sa-dataform.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud iam service-accounts add-iam-policy-binding \
  dataform-runner@ford-training-430008.iam.gserviceaccount.com \
  --member="serviceAccount:service-227551883136@gcp-sa-dataform.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator"
```

Példa saját felhasználóra:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  dataform-runner@ford-training-430008.iam.gserviceaccount.com \
  --member="user:<your_google_account_email>" \
  --role="roles/iam.serviceAccountUser"
```

Ha a `create_dataform_workflow_invocation` task ezt a hibát adja:

```text
Service account must be set when strict act as checks are enabled.
```

akkor ellenőrizd, hogy a `dataform_service_account` változó nem a default Dataform service agentre mutat-e, hanem custom service accountra.

---

## 8. Első futtatás: `sales_export_dag`

Először ezt futtasd:

```text
sales_export_dag
```

Ez a DAG feltételezi, hogy a `sales_gold` már létezik.

Lépések:

1. Nyisd meg az Airflow UI-t.
2. Keresd meg a `sales_export_dag` DAG-ot.
3. Unpause-old, ha szükséges.
4. Triggereld manuálisan.
5. Figyeld meg a Graph vagy Grid nézetet.
6. Nyisd meg a task logokat.

Várt task sorrend:

```text
check_sales_gold
  ↓
trigger_cloud_run_exporter
  ↓
verify_export_file
```

Sikeres futás esetén:

- a BigQuery GOLD tábla nem üres,
- a Cloud Run exporter létrehoz egy Excel fájlt,
- az Airflow ellenőrzi, hogy a fájl létezik és nem üres,
- az export fájl megjelenik a bucket `export/` folderében.

A UI-ban érdemes megmutatni:

- a Graph nézetben hogyan követik egymást a taskok,
- a `trigger_cloud_run_exporter` task XCom értékében hogyan jelenik meg az exporter JSON válasza,
- a `verify_export_file` task logjában hogyan látszik az ellenőrzött Cloud Storage objektum,
- mi történik, ha egy upstream task hibázik: a downstream taskok nem indulnak el.

---

## 9. Második futtatás: `sales_dataform_export_dag`

Ha a Dataform változók is be vannak állítva, futtasd:

```text
sales_dataform_export_dag
```

Várt task sorrend:

```text
create_dataform_compilation_result
  ↓
create_dataform_workflow_invocation
  ↓
wait_for_dataform_workflow_invocation
  ↓
check_sales_gold
  ↓
trigger_cloud_run_exporter
  ↓
verify_export_file
```

Itt már azt látjuk, hogy az Airflow:

- elindítja a Dataform pipeline-t,
- megvárja a Dataform futás végét,
- csak sikeres Dataform után engedi tovább az exportot,
- hibánál megállítja a downstream taskokat.

Ez egy jó pont arra, hogy a Graph nézetben megmutassuk:

- melyik task fut,
- melyik várakozik,
- hol történt hiba,
- mit jelent a retry,
- hogyan lehet újrafuttatni csak egy taskot.

Ebben a DAG-ban különösen hasznos megfigyelni:

- a Dataform futás Airflowban egyetlen taskként látszik, de Dataformon belül több SQLX action futhat,
- a `wait_for_dataform_workflow_invocation` task nem dolgozza fel az adatot, csak vár és állapotot ellenőriz,
- a Cloud Run exporter csak akkor indul, ha a Dataform futás sikeres,
- a pipeline végén nem csak azt hisszük, hogy készült export, hanem ellenőrizzük is a fájlt Cloud Storage-ban.

---

## 10. Mit érdemes élőben demonstrálni?

### Harmadik futtatás: `parallel_market_exports_dag`

Ez a DAG a fan-out / fan-in mintát mutatja meg.

Várt task sorrend:

```text
check_sales_gold
  ↓
prepare_export_requests
  ↓
export_market_hu   export_market_cz   export_market_sk   export_all_markets
       \                 |                  |                    /
        \                |                  |                   /
         v               v                  v                  v
                    collect_export_results
                              ↓
                    verify_all_export_files
                              ↓
                    final_success_notification
```

Taskok szerepe:

| Task | Mit csinál? | Miért jó tréningpélda? |
|---|---|---|
| `check_sales_gold` | Ellenőrzi, hogy a GOLD tábla nem üres. | Nem indítunk párhuzamos exportokat, ha nincs mit exportálni. |
| `prepare_export_requests` | Összerakja a különböző export payloadokat: HU, CZ, SK és teljes export. | Megmutatja, hogy az Airflow tud előkészített paramétereket továbbadni XComon keresztül. |
| `export_market_hu` / `export_market_cz` / `export_market_sk` / `export_all_markets` | Ugyanazt a Cloud Run exportert hívják meg különböző filterekkel. | Ez a fan-out rész: több független task párhuzamosan fut. |
| `collect_export_results` | Összegyűjti az összes exporter válaszát. | Ez a fan-in kezdete: egy közös task bevárja az összes párhuzamos exportot. |
| `verify_all_export_files` | Minden exportált `gs://...xlsx` fájlt ellenőriz Cloud Storage-ban. | Megmutatja, hogy nem elég elindítani a párhuzamos munkát, az eredményt is közösen validálni kell. |
| `final_success_notification` | Logba kiírja az összes sikeres export URI-ját. | Egyszerű, setup nélküli notification minta. |

Ez a DAG azért látványos, mert a Graph nézetben tényleg szétnyílik a pipeline, majd újra összezár.

A `demo_task_delay_seconds` változó miatt a taskok nem futnak le azonnal. Így a Grid és Graph nézetben jól megfigyelhető:

- melyik task fut párhuzamosan,
- mikor várakozik a közös gyűjtő task,
- hogyan állna meg a pipeline, ha az egyik export hibázna,
- hogy a végső notification csak az összes sikeres export után fut.

### Negyedik futtatás: `branching_market_export_dag`

Ez a DAG a branching mintát mutatja meg.

Várt logika:

```text
check_sales_gold
  ↓
choose_export_strategy
  ├─ ha row_count <= threshold → export_all_markets
  └─ ha row_count > threshold  → export_market_hu → export_market_cz → export_market_sk
  ↓
join_selected_branch
  ↓
verify_selected_exports
  ↓
final_branching_notification
```

Taskok szerepe:

| Task | Mit csinál? | Miért jó tréningpélda? |
|---|---|---|
| `check_sales_gold` | Megszámolja a GOLD tábla sorait. | Valós adatállapot alapján döntünk, nem kézi kapcsolóval. |
| `choose_export_strategy` | Visszaadja a kiválasztott következő task `task_id`-ját: `export_all_markets` vagy `export_market_hu`. | Ez a BranchPythonOperator lényege: a DAG futás közben választ útvonalat, a nem választott közvetlen downstream task pedig `skipped` lesz. |
| `export_all_markets` | Egy teljes exportot készít. | Egyszerűbb ág, ha kevés az adat. |
| `export_market_hu` / `export_market_cz` / `export_market_sk` | Sorban több exportot indít market filterrel. | Megmutatja, hogy az egyik branch lehet hosszabb, több taskból álló útvonal. |
| `join_selected_branch` | Visszazárja az ágakat. | Megmutatja a `NONE_FAILED_MIN_ONE_SUCCESS` trigger rule szerepét. |
| `verify_selected_exports` | Csak a kiválasztott ág exportjait validálja. | Branching után a skipelt taskokkal is számolni kell. |
| `final_branching_notification` | Kiírja, mely exportok készültek el. | A végén egy helyen látszik a választott út eredménye. |

Élő demóhoz érdemes kétszer futtatni:

1. `branching_export_row_threshold = 100`
2. `branching_export_row_threshold = 999999`

Így nagy eséllyel egyszer a marketenkénti ág, egyszer pedig az egyben exportáló ág fut. A Graph nézetben jól látszik, hogy a nem választott ágak `skipped` állapotba kerülnek.

### Ötödik futtatás: `pipeline_with_notifications_dag`

Ez a DAG a success / failure notification mintát mutatja meg.

Várt fő folyamat:

```text
start_pipeline
  ↓
create_dataform_compilation_result
  ↓
create_dataform_workflow_invocation
  ↓
wait_for_dataform_workflow_invocation
  ↓
check_sales_gold
  ↓
trigger_cloud_run_exporter
  ↓
verify_export_file
  ↓
success_notification
```

Hiba esetén:

```text
any failed pipeline task
  ↓
failure_notification
```

Taskok szerepe:

| Task | Mit csinál? | Miért jó tréningpélda? |
|---|---|---|
| `start_pipeline` | Logba kiírja a pipeline indulását és a DAG run azonosítót. | Megmutatja, hogy lehet explicit pipeline kezdőpontot használni. |
| Dataform taskok | Compile, workflow invocation, majd Dataform futás megvárása. | Ugyanazt az end-to-end transformation mintát használja, mint a fő Dataform DAG. |
| `check_sales_gold` | GOLD ellenőrzési kapu. | Példa arra, hogy notification előtt is érdemes validálni az eredményt. |
| `trigger_cloud_run_exporter` | Meghívja a Cloud Run exportert. | Külső service indítása sikeres transformation után. |
| `verify_export_file` | Ellenőrzi a Cloud Storage export fájlt. | A pipeline végállapotát objektíven ellenőrzi. |
| `success_notification` | Csak teljes siker esetén fut, és kiírja az export URI-t. | Egyszerű success notification minta. |
| `failure_notification` | Ha bármelyik fő pipeline task hibázik, kiírja a failed taskokat. | Megmutatja, hogyan lehet failure ágat építeni trigger rule-lal. |

Ez a DAG azért hasznos, mert átvezet az üzemeltetési gondolkodásba. A résztvevők látják, hogy egy pipeline nem csak feldolgozásból áll, hanem státuszkommunikációból is.

Most a notification csak Airflow logba ír. Ez szándékos, mert nem akarunk Slack, Teams vagy email setupot behozni a tréningbe. Production környezetben ugyanez a pattern továbbvihető:

- Slack webhookra,
- Teams webhookra,
- emailre,
- Pub/Sub üzenetre,
- incident management rendszerre.

### Hatodik futtatás: `bigquery_operator_showcase_dag`

Ez az opcionális DAG azt mutatja meg, hogyan néz ki egy natív Google provider operator használata.

Várt folyamat:

```text
start
  ↓
check_sales_gold_with_bigquery_operator
  ↓
visual_pause
  ↓
operator_summary
```

Futtatás előtt ellenőrizd:

- az `_PIP_ADDITIONAL_REQUIREMENTS` tartalmazza az `apache-airflow-providers-google` csomagot,
- létezik a `google_cloud_default` Airflow connection,
- a `gcp_conn_id` változó értéke `google_cloud_default`,
- a `bigquery_location` változó a BigQuery dataset régiója, például `europe-west4`.

Ez a DAG nem új üzleti logikát tanít, hanem azt, hogy Airflowban nem kell mindent `PythonOperator`-ral megírni. Ha van jól illeszkedő provider operator, akkor az tisztább és olvashatóbb lehet.

### Sikeres export

Futtasd a `sales_export_dag`-ot, majd nézd meg:

```bash
gsutil ls gs://training-jani/export/
```

Vagy a Cloud Console-ban a bucket `export/` folderét.

### Hibás BigQuery konfiguráció

Állítsd át ideiglenesen a `gold_dataset` változót egy nem létező datasetre.

A `check_sales_gold` task el fog hasalni. Ez jól mutatja, hogy Airflowban hol jelenik meg a hiba és hogyan olvasható a task log.

### Hibás Cloud Run URL

Állítsd át ideiglenesen a `cloud_run_exporter_url` változót rossz URL-re.

A `trigger_cloud_run_exporter` task fog hibázni, a `verify_export_file` pedig nem indul el.

### Dataform hiba

Ha a Dataform workspace-ben hibás SQLX vagy rossz `workflow_settings.yaml` van, a `wait_for_dataform_workflow_invocation` task fog hibát jelezni.

Ez jól mutatja, hogy Airflow nem nyeli el a downstream rendszer hibáját, hanem orchestration szinten láthatóvá teszi.

---

## 11. Miért nem Airflow indítja az importert?

A 3. napi importer event-driven patternre épül:

```text
Cloud Storage upload
      ↓
Pub/Sub notification
      ↓
Cloud Run importer
      ↓
BigQuery RAW
```

Ez jó architecture, ezért nem érdemes csak az Airflow kedvéért lecserélni.

A 4. napi DAG-ok inkább ezt mutatják:

```text
RAW már frissült event-driven módon
      ↓
Airflow elindítja a Dataform pipeline-t
      ↓
Airflow ellenőrzi a GOLD eredményt
      ↓
Airflow meghívja a Cloud Run exportert
      ↓
Airflow ellenőrzi az export fájlt
```

Így a résztvevők két fontos mintát látnak:

- event-driven ingestion,
- scheduled vagy manual orchestration.

Ez közelebb áll a valós rendszerekhez, mint ha mindent egyetlen monolit DAG-ba erőltetnénk.

---

## 12. Cleanup és biztonság

A lokális Airflow leállítása:

```bash
docker compose down
```

Ha teljesen törölni szeretnéd a lokális Airflow állapotot:

```bash
docker compose down --volumes --remove-orphans
```

Figyelem: ez törli az Airflow metadata adatbázist is, tehát elvesznek a DAG run historyk és Variables beállítások.

A credential fájl:

```text
config/application_default_credentials.json
```

maradjon lokálisan, és ne kerüljön Gitbe.

---

## Mit építettünk?

A nap végére a lokális Airflow már nem csak egy teszt DAG-ot futtat, hanem valódi GCP komponenseket koordinál:

```text
Lokális Airflow
   ↓
Dataform API
   ↓
BigQuery GOLD
   ↓
Cloud Run exporter
   ↓
Cloud Storage export
```

A lényeg: az Airflow nem váltja ki a Cloud Run, BigQuery vagy Dataform szerepét. Az Airflow a pipeline karmestere: indít, vár, ellenőriz, hibát jelez és újrafuttathatóvá teszi a folyamatot.
