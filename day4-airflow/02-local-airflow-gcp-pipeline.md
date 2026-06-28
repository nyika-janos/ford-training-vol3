# 02 - Lokális Airflow DAG-ok GCP komponensekkel

## Cél

Ebben a részben a lokális Airflow környezetből hívunk meg valódi GCP komponenseket.

Az előző napok végére már működött:

- Cloud Storage fájlfeltöltésből induló Cloud Run importer,
- RAW réteg betöltése BigQuery-be,
- Dataform transformation pipeline,
- Cloud Run exporter,
- Excel export Cloud Storage-ba.

Most nem új adatfeldolgozó logikát írunk. Az Airflow feladata az lesz, hogy a meglévő komponenseket sorrendbe tegye, indítsa, ellenőrizze és láthatóvá tegye.

---

## Mitől más ez lokális Airflowból?

Cloud Composerben az Airflow GCP-n belül fut. Lokális Dockeres Airflow esetén viszont az Airflow konténerek a saját gépeden futnak.

Ez három fontos különbséget jelent:

| Téma | Cloud Shell / Composer | Lokális Airflow Dockerben |
|---|---|---|
| GCP autentikáció | sokszor adott a környezetből | külön be kell vinni a konténerbe |
| Python csomagok | előre telepítve vagy image-ben kezelve | nekünk kell telepíteni |
| Hálózat | GCP-n belül fut | a saját gépedről hívja a GCP API-kat |

Ezért a DAG-ok előtt be kell állítani:

- Google Application Default Credentials,
- szükséges Python csomagok,
- Airflow Variables,
- GCP jogosultságok.

---

## Javasolt DAG stratégia

Két DAG-ot készítünk.

### 1. `sales_export_dag`

Ez az egyszerűbb, elsőként futtatandó DAG.

Flow:

```text
check_sales_gold
      |
      v
trigger_cloud_run_exporter
      |
      v
verify_export_file
```

Mit mutat meg?

- BigQuery ellenőrzés Airflow taskból
- Cloud Run exporter HTTP hívása Airflowból
- Cloud Storage export fájl ellenőrzése
- task dependency
- retry
- XCom alapú értékátadás
- task logok

Ez jó első GCP-s Airflow demo, mert a Dataform repository adatok nélkül is működik, ha a `sales_gold` tábla már létezik.

### 2. `sales_dataform_export_dag`

Ez a nagyobb pipeline DAG.

Flow:

```text
create_dataform_compilation_result
      |
      v
create_dataform_workflow_invocation
      |
      v
wait_for_dataform_workflow_invocation
      |
      v
check_sales_gold
      |
      v
trigger_cloud_run_exporter
      |
      v
verify_export_file
```

Mit mutat meg?

- Dataform API hívás Airflowból
- Dataform compilation result létrehozása
- Dataform workflow invocation indítása
- hosszabb futás pollolása
- Dataform után Cloud Run exporter indítása
- end-to-end orchestration

Fontos: az importer továbbra is event-driven módon működik. Ha új fájlt töltünk a bucket `landing/` folderébe, akkor a Pub/Sub indítja a Cloud Run importert. Az Airflow ebben a gyakorlatban a transformation és export szakaszt koordinálja.

---

## 1. DAG fájlok

A repositoryban a DAG-ok itt vannak:

```text
day4-airflow/materials/dags/sales_export_dag.py
day4-airflow/materials/dags/sales_dataform_export_dag.py
```

Másold őket a lokális Airflow projekt `dags` mappájába.

Ha az első gyakorlat szerint dolgoztál:

```bash
cp ~/ford-training-vol3/day4-airflow/materials/dags/sales_export_dag.py ~/gcp-training-airflow/dags/
cp ~/ford-training-vol3/day4-airflow/materials/dags/sales_dataform_export_dag.py ~/gcp-training-airflow/dags/
```

Windows PowerShell példa:

```powershell
copy .\day4-airflow\materials\dags\sales_export_dag.py $HOME\gcp-training-airflow\dags\
copy .\day4-airflow\materials\dags\sales_dataform_export_dag.py $HOME\gcp-training-airflow\dags\
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

Windows PowerShellben szerkesztheted VS Code-dal is:

```powershell
code .env
```

Megjegyzés: ez tréninghez kényelmes megoldás. Production Airflow környezetben inkább saját Docker image-be tennénk a dependencyket.

---

## 3. GCP autentikáció lokális Airflowhoz

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

## 4. `docker-compose.yaml` módosítása

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

## 5. GCP jogosultságok

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

## 6. Airflow Variables beállítása

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

Az exporter URL-t így tudod lekérdezni Cloud Shellben vagy olyan gépen, ahol van `gcloud`:

```bash
gcloud run services describe data-exporter \
  --region europe-west4 \
  --format='value(status.url)'
```

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

## 7. Első futtatás: `sales_export_dag`

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

---

## 8. Második futtatás: `sales_dataform_export_dag`

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

---

## 9. Mit érdemes élőben demonstrálni?

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

## 10. Miért nem Airflow indítja az importert?

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

## 11. Cleanup és biztonság

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
