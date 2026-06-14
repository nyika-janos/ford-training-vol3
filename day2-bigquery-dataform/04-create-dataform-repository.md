# 04 - Dataform repository létrehozása

## Cél

Ebben a gyakorlatban létrehozunk egy Dataform repositoryt, és előkészítjük a developmenthez.

Nem írunk SQL-t az alapoktól.

Ehelyett egy előre elkészített repository structure-t használunk, amely már tartalmazza a training során használt Dataform modelleket.

Az előkészített repository fájlok ebben a training repositoryban, az alábbi helyen találhatók:

```text
day2-bigquery-dataform/materials/dataform
```

A gyakorlat végére rendelkezel majd az alábbival:

```text
<your_name>_training_dataform
```

amely csatlakozik a BigQueryhez, és készen áll a developmentre.

---

# Miért csináljuk ezt?

Eddig létrehoztuk a RAW layert:

```text
CSV Files
    ↓
BigQuery RAW Tables
```

A következő lépés az adatok átalakítása egy reporting-ready warehouse-zá.

Az Alteryxben ezt az alábbi toolokkal valósítanánk meg:

- Select
- Formula
- Filter
- Join
- Summarize

Ezeket egy workflow-ban kapcsolnánk össze.

A GCP-ben ugyanezt a logicot az alábbiakkal valósítjuk meg:

```text
BigQuery
+
Dataform
```

---

# Mi a Dataform?

A Dataform egy GCP-native transformation framework.

Az alábbiakban segít:

- SQL-kód rendszerezése
- Újrafelhasználható transformation pipeline-ok létrehozása
- Dependencyk kezelése
- Data quality checkek létrehozása
- Warehouse layerek építése

A tényleges processinget továbbra is a BigQuery végzi.

A Dataform orchestrálja és kezeli a transformationöket.

---

# A Dataform megnyitása

Navigálj ide:

```text
Dataform
```

a Google Cloud Console-ban.

---

# Repository létrehozása

Kattints erre:

```text
Create Repository
```

Repository name:

```text
<your_name>_training_dataform
```

Példa:

```text
janos_training_dataform
```

Region:

```text
europe-west4
```

---

# Git integration

Ehhez a gyakorlathoz válaszd ki:

```text
Create without a remote repository
```

A training fájlokat manuálisan importáljuk.

Később, valós projectekben a Dataform repositorykat általában a GitHubhoz vagy a GitLabhoz csatlakoztatják.

---

# Workspace létrehozása

A repository létrehozása után:

Kattints erre:

```text
Create Workspace
```

Workspace name:

```text
development
```

Nyisd meg a workspace-t.

---

# A repository structure áttekintése

Az alábbihoz hasonló structure-t kell látnod:

```text
definitions/
includes/
workflow_settings.yaml
```

---

# A workflow_settings.yaml konfigurálása

Nyisd meg:

```text
workflow_settings.yaml
```

Cseréld le a tartalmát erre:

```yaml
defaultProject: ford-training-430008
defaultLocation: europe-west4
defaultAssertionDataset: assertions

vars:
  username: "janos"
```

Cseréld le ezt:

```text
janos
```

a saját keresztnevedre.

Példák:

```yaml
vars:
  username: "barni"
```

```yaml
vars:
  username: "tianze"
```

```yaml
vars:
  username: "adam"
```

---

# Miért itt tároljuk a username-et?

A training során minden résztvevő saját datasetekkel rendelkezik:

```text
janos_raw
janos_stage
janos_gold
```

or:

```text
barni_raw
barni_stage
barni_gold
```

Ahelyett, hogy ezeket a neveket a teljes projectben hardcode-olnánk, egyszer tároljuk a username-et, és minden mást automatikusan generálunk.

---

# A training repository letöltése

Nyisd meg:

[ford-training-vol3-day2-dataform-repo](https://github.com/nyika-janos/ford-training-vol3-day2-dataform-repo?utm_source=chatgpt.com)

Töltsd le:

```text
Code
↓
Download ZIP
```

Csomagold ki az archívumot lokálisan.

---

# A repository structure áttekintése

A letöltött repositoryban az alábbiakat találod:

```text
definitions/
includes/
```

A fájlokat már előkészítettük ehhez a traininghez.

---

# A training fájlok feltöltése

Másold át ennek a tartalmát:

```text
definitions/
```

a letöltött repositoryból a Dataform repositorydba.

Másold át ennek a tartalmát:

```text
includes/
```

a Dataform repositorydba.

A structure-nek most így kell kinéznie:

```text
definitions/
├── dealer_stage.sqlx
├── mapping_stage.sqlx
├── sales_stage.sqlx
├── sales_enrich.sqlx
└── sales_gold.sqlx

includes/
└── config.js
```

---

# Az includes/config.js áttekintése

Nyisd meg:

```text
includes/config.js
```

Ez a fájl automatikusan generálja a datasetneveket az alábbi fájlban tárolt username alapján:

```yaml
workflow_settings.yaml
```

Például ez:

```yaml
username: "janos"
```

automatikusan ezt eredményezi:

```text
janos_raw
janos_stage
janos_gold
```

Ez a megközelítés elkerüli a datasetnevek hardcode-olását a teljes projectben.

---

# A model structure áttekintése

Nyisd meg:

```text
sales_stage.sqlx
```

Figyeld meg:

```sql
schema: require("../includes/config").stage_dataset
```

A datasetnév dinamikusan jön létre.

Ugyanezt a patternt használjuk a teljes repositoryban.

---

# A repository compile-olása

Kattints erre:

```text
Compile
```

A compilationnek sikeresen be kell fejeződnie.

Ha a compilation sikertelen:

- ellenőrizd a username-et
- ellenőrizd a `workflow_settings.yaml` fájlt
- ellenőrizd, hogy minden fájlt megfelelően másoltál-e át

---

# Checkpoint

Mostanra rendelkezned kell az alábbiakkal:

✓ Dataform repository

✓ Development workspace

✓ Konfigurált `workflow_settings.yaml`

✓ Importált `definitions`

✓ Importált `includes`

✓ Sikeres compilation

---

# Mi következik?

A következő gyakorlatban áttekintjük a STAGE modelleket, és futtatjuk az első transformationöket.

Megtisztítjuk és standardizáljuk a RAW adatokat a business logic alkalmazása előtt.
