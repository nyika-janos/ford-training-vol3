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

Több DAG-ot készítünk, de nem mindegyik ugyanazt tanítja.

Az első DAG-ok szándékosan sok `PythonOperator` taskot használnak. Ennek oka, hogy lokális Airflowból, minimális extra provider setup mellett akartunk GCP API-kat és Cloud Run HTTP endpointokat hívni.

Production Airflow vagy Cloud Composer környezetben viszont gyakran használnánk provider operatorokat is, például:

- BigQuery operatorokat,
- Dataform operatorokat,
- Cloud Run operatorokat,
- sensorokat.

Ezért külön van egy kicsi operator showcase DAG is, ahol BigQuery operátort használunk.

Megjegyzés: a `hello_training_dag` az 01-es lokális Airflow setup ellenőrző példája. A 02-es anyagban már a GCP komponenseket hívó DAG-okkal foglalkozunk.

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

Taskok szerepe:

| Task | Mit csinál? | Miért jó tréningpélda? |
|---|---|---|
| `check_sales_gold` | BigQuery queryvel megszámolja a GOLD tábla sorait. Ha a tábla üres, hibára fut. | Megmutatja, hogy Airflow taskkal egyszerű data quality gate-et lehet építeni. |
| `trigger_cloud_run_exporter` | HTTP POST kéréssel meghívja a 3. napon deployolt Cloud Run exportert. | Megmutatja, hogyan indít Airflow külső service-t, miközben maga nem exportál Excel fájlt. |
| `verify_export_file` | A Cloud Run válaszában kapott `gs://...` útvonal alapján ellenőrzi, hogy az export fájl tényleg létrejött és nem üres. | Megmutatja, hogyan lehet downstream ellenőrzést tenni egy service hívás után. |

Ez a DAG szándékosan kicsi. A résztvevők jól látják benne az Airflow alapmintát:

```text
ellenőrzés
  ↓
külső komponens indítása
  ↓
eredmény ellenőrzése
```

Ez a legtöbb orchestration workflow alaplogikája.

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

Taskok szerepe:

| Task | Mit csinál? | Miért jó tréningpélda? |
|---|---|---|
| `create_dataform_compilation_result` | Dataform API-n keresztül compile-olja a Dataform projektet. Workspace vagy Git branch alapján készít compilation resultot. | Megmutatja, hogy a Dataform futtatás előtt először le kell fordítani a SQLX projektet végrehajtható tervvé. |
| `create_dataform_workflow_invocation` | A compilation resultból Dataform workflow invocationt indít. Itt adjuk meg a custom futtató service accountot is. | Megmutatja, hogyan indít Airflow GCP-native transformation pipeline-t anélkül, hogy SQL-t futtatna saját maga. |
| `wait_for_dataform_workflow_invocation` | Pollolja a Dataform workflow állapotát, amíg `SUCCEEDED`, `FAILED` vagy `CANCELLED` nem lesz. | Megmutatja a hosszabb külső futások Airflowból történő várakoztatását és hibakezelését. |
| `check_sales_gold` | Ellenőrzi, hogy a Dataform futás után a GOLD tábla tartalmaz adatot. | Megmutatja, hogy transformation után érdemes ellenőrzési kaput tenni. |
| `trigger_cloud_run_exporter` | Sikeres Dataform után meghívja a Cloud Run exportert. | Megmutatja a komponensek közötti függőséget: export csak friss GOLD réteg után indul. |
| `verify_export_file` | Ellenőrzi a Cloud Storage-ba írt Excel exportot. | Megmutatja az end-to-end pipeline végállapotának ellenőrzését. |

Ez a DAG már közelebb áll egy valós pipeline-hoz:

```text
transformation terv létrehozása
  ↓
transformation futtatása
  ↓
futás megvárása
  ↓
eredmény ellenőrzése
  ↓
export indítása
  ↓
export ellenőrzése
```

A fontos tanulság: az Airflow nem veszi át sem a Dataform, sem a Cloud Run szerepét. Airflow koordinál:

- mikor mi induljon,
- mire kell várni,
- hol álljon meg hiba esetén,
- mit lehet újrafuttatni,
- hol nézzük meg a logokat.

### 3. `parallel_market_exports_dag`

Ez a DAG a fan-out / fan-in mintát mutatja meg.

Flow:

```text
check_sales_gold
      |
      v
prepare_export_requests
      |
      v
export_market_hu   export_market_cz   export_market_sk   export_all_markets
       \                 |                  |                    /
        \                |                  |                   /
         v               v                  v                  v
                    collect_export_results
                              |
                              v
                    verify_all_export_files
                              |
                              v
                    final_success_notification
```

Taskok szerepe:

| Task | Mit csinál? | Miért jó tréningpélda? |
|---|---|---|
| `check_sales_gold` | Ellenőrzi, hogy a GOLD tábla nem üres. | Nem indítunk több exportot, ha nincs mit exportálni. |
| `prepare_export_requests` | Előkészíti a HU, CZ, SK és teljes export payloadjait. | Megmutatja az XCom alapú paraméterátadást több downstream task felé. |
| `export_market_hu` / `export_market_cz` / `export_market_sk` / `export_all_markets` | Ugyanazt a Cloud Run exportert hívják különböző payloadokkal. | Ez a fan-out rész: több független task párhuzamosan futhat. |
| `collect_export_results` | Összegyűjti az összes export task válaszát. | Ez a fan-in rész: egy közös task bevárja a párhuzamos ágakat. |
| `verify_all_export_files` | Ellenőrzi, hogy minden export fájl tényleg létrejött Cloud Storage-ban. | Megmutatja, hogy a párhuzamos munkák eredményét közösen is validálni kell. |
| `final_success_notification` | Kiírja az összes sikeres export URI-ját. | Egyszerű notification minta több eredmény összegzése után. |

Ez a DAG azért látványos, mert a Graph nézetben tényleg szétnyílik a pipeline, majd újra összezár.

### 4. `branching_market_export_dag`

Ez a DAG a feltételes elágazást mutatja meg.

Flow:

```text
check_sales_gold
      |
      v
choose_export_strategy
   /                         \
  v                           v
export_all_markets        export_market_hu
                              |
                              v
                           export_market_cz
                              |
                              v
                           export_market_sk
  \                           /
   v                         v
join_selected_branch
      |
      v
verify_selected_exports
      |
      v
final_branching_notification
```

Taskok szerepe:

| Task | Mit csinál? | Miért jó tréningpélda? |
|---|---|---|
| `check_sales_gold` | Megszámolja a GOLD tábla rekordjait. | A döntés nem kézzel történik, hanem adatállapot alapján. |
| `choose_export_strategy` | `BranchPythonOperator`: ha a rekordok száma nagyobb, mint a threshold, a marketenkénti ágra lép; különben az egyben exportáló ágra. | Megmutatja, hogyan lehet egy DAG-ban feltételes útvonalakat kezelni. |
| `export_all_markets` | Egyetlen teljes exportot indít. | Ez a “kis adatmennyiség” ág. |
| `export_market_hu` / `export_market_cz` / `export_market_sk` | Egymás után marketenként exportál. | Ez a “nagyobb adatmennyiség” ág, ahol más feldolgozási útvonalat választunk. |
| `join_selected_branch` | Bevárja azt az ágat, amelyiket a branch kiválasztotta. | Megmutatja, hogy branching után speciális trigger rule kell a visszazáráshoz. |
| `verify_selected_exports` | Csak a ténylegesen lefutott exportok fájljait ellenőrzi. | Megmutatja, hogy a skipelt ágakkal számolni kell. |
| `final_branching_notification` | Logba kiírja a sikeres exportokat. | Egyszerű notification minta branching után. |

Ez a DAG azért hasznos, mert egy gyakori pipeline döntést modellez:

```text
kevés adat → egyszerű út
sok adat → marketenkénti út
```

A threshold alapértelmezésben `100`, de a `branching_export_row_threshold` Airflow Variable átírásával könnyen demonstrálható mindkét ág.

Fontos Airflow működés: a `BranchPythonOperator` nem boolean értéket ad vissza. Annak a következő tasknak a `task_id`-ját adja vissza, amelyik ágon tovább kell menni.

Ebben a DAG-ban:

```python
if row_count > threshold:
    return "export_market_hu"

return "export_all_markets"
```

Ha például `row_count = 150` és `threshold = 100`, akkor a task az `export_market_hu` értéket adja vissza. Ekkor Airflow az `export_market_hu` ágat indítja el, az ugyanonnan induló másik közvetlen ágat, vagyis az `export_all_markets` taskot pedig automatikusan `skipped` állapotba teszi.

Ezért kell a visszazáró tasknál speciális trigger rule:

```python
trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
```

Branchingnél ugyanis normális, hogy az egyik ág `skipped`. A join tasknak ezért nem azt kell várnia, hogy minden upstream task sikeres legyen, hanem azt, hogy legalább egy kiválasztott ág sikeresen lefusson, és ne legyen hiba.

### 5. `pipeline_with_notifications_dag`

Ez a DAG a sikeres és sikertelen lezárási ágakat mutatja meg.

Flow:

```text
start_pipeline
      |
      v
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
      |
      v
success_notification

failure_notification oldalág: bármely fontos upstream hiba esetén fut
```

Taskok szerepe:

| Task | Mit csinál? | Miért jó tréningpélda? |
|---|---|---|
| `start_pipeline` | `EmptyOperator`, vizuális kezdőpont. | A Graph nézetben tisztábbá teszi a pipeline elejét. |
| Dataform taskok | Compile, invocation indítás, majd várakozás. | Ugyanazt az end-to-end transformation részt mutatja, mint a nagy Dataform DAG. |
| Export taskok | GOLD ellenőrzés, exporter hívás, fájlvalidáció. | Megmutatja, hogy a sikeres transformation után indulhat az export. |
| `success_notification` | Csak akkor fut, ha a pipeline sikeresen végigért. | Sikeres lezárási pontot ad a DAG-nak. |
| `failure_notification` | `TriggerRule.ONE_FAILED` alapján fut, ha valamelyik figyelt task hibázik. | Megmutatja, hogyan lehet Airflowban failure notification ágat építeni külső email/Slack setup nélkül is. |

Ez jó tréningpélda arra, hogy egy pipeline-nak nem csak üzleti lépései vannak, hanem operációs lezárása is: siker esetén összegzés, hiba esetén diagnosztikai üzenet.

### 6. `bigquery_operator_showcase_dag`

Ez egy opcionális, kicsi DAG, amely azt mutatja meg, hogyan néz ki egy natív Airflow provider operator használata.

Flow:

```text
start
  ↓
check_sales_gold_with_bigquery_operator
  ↓
visual_pause
  ↓
operator_summary
```

Taskok szerepe:

| Task | Mit csinál? | Miért jó tréningpélda? |
|---|---|---|
| `start` | `EmptyOperator`, csak vizuális kezdőpont. | Megmutatja, hogy nem minden tasknak kell tényleges munkát végeznie. |
| `check_sales_gold_with_bigquery_operator` | `BigQueryCheckOperator` segítségével ellenőrzi, hogy a GOLD tábla nem üres. | Megmutatja, hogy BigQuery ellenőrzéshez nem kell saját Python client kódot írni. |
| `visual_pause` | `BashOperator` segítségével rövid várakozást tesz a DAG-ba. | Megmutatja egy standard, nem Python alapú operátor használatát. |
| `operator_summary` | Rövid összefoglalót ír a logba. | Itt a PythonOperator már csak emberi olvashatóságot ad, nem a BigQuery munkát végzi. |

Ez a DAG jó válasz arra a kérdésre, hogy:

```text
Airflowban mindent PythonOperatorral kell csinálni?
```

Nem. A PythonOperator rugalmas, de ha van jól illeszkedő provider operator, akkor az sokszor tisztább.

Megjegyzés: ebben a DAG-ban a BigQuery operator `location`, `gcp_conn_id` és tábla paramétereit Pythonból olvassuk ki Airflow Variable-ből. Ennek oka, hogy nem minden provider operator minden paramétere Jinja-template mező. Ha egy nem template-elt mezőbe `{{ var.value... }}` kerül, akkor az szó szerint jut el a GCP API-ig.

### Miért nem Dataform operátorral kezdtünk?

Airflow Google providerben léteznek Dataform operatorok is. A tréning közben viszont több környezeti részletet kellett kézben tartani:

- lokális Airflow konténer,
- Application Default Credentials,
- strict act-as mode,
- custom Dataform service account,
- workspace-alapú compile,
- Airflow 3 kompatibilitás.

Ezért a Dataform DAG-ban direkt API-hívásos mintát használunk. Így pontosan látszik, mi történik:

```text
create compilation result
create workflow invocation
poll workflow invocation state
```

Miután ez érthető, később ugyanennek egy részét Dataform provider operatorokra lehet cserélni.

---

## Gyakorlati futtatás

A konkrét másolási, dependency, GCP auth, Airflow Variable és futtatási lépések külön runbookba kerültek:

[03-local-airflow-gcp-runbook.md](03-local-airflow-gcp-runbook.md)
