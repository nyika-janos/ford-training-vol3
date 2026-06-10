# Day 2 - Dataform Workspace és Repository működése

## Git kapcsolat

A modern Dataform projektek szinte mindig Git repositoryhoz kapcsolódnak.

Tipikusan:

- GitHub
- GitLab
- Bitbucket

A repository lesz a fejlesztés egyetlen forrása (Single Source of Truth).

A Dataform nem a saját adatbázisában tárolja a modelleket.

Valójában a Git repository tartalmazza:

- SQLX fájlokat
- assertionöket
- konfigurációkat
- workflow definíciókat

A Dataform ezekből dolgozik.

---

## Mit mutassunk a felületen?

Dataform

↓

Repositories

↓

Repository Settings

↓

Git Repository

---

Mutassuk meg:

- Git provider
- branch
- commit hash

---

## Miért fontos?

Minden változás:

- visszakereshető
- auditálható
- visszagörgethető

Ez jelentős előrelépés a klasszikus Alteryx workflow-khoz képest.

---

# Workspace

## Mi az a Workspace?

A Workspace a fejlesztői környezet.

Itt történik:

- új modellek létrehozása
- módosítás
- tesztelés
- debugolás

Mielőtt bármi Production környezetbe kerülne, itt dolgozunk vele.

---

## Mit mutassunk?

Repository

↓

Workspaces

↓

Saját Workspace

---

A résztvevők itt fogják szerkeszteni a SQLX fájlokat.

---

# Release Configuration

Ez az egyik legfontosabb Dataform objektum.

Sok kezdő teljesen kihagyja.

---

## Mi a szerepe?

A Release Configuration mondja meg:

- melyik branch-ből építünk
- melyik commitot használjuk
- melyik környezetbe publikálunk

Például:

```text
main
```

branch.

---

## Mit mutassunk?

Release Configurations

---

Mutassuk meg:

- branch
- release schedule
- compilation result

---

# Compilation Result

Ez a Dataform egyik legfontosabb fogalma.

A Release során Dataform:

1. beolvassa a repositoryt
2. felépíti a dependency graphot
3. SQLX → SQL fordítást végez

Az eredmény:

Compilation Result

---

## Mit mutassunk?

Compilation Result

↓

Graph

↓

Generated SQL

---

Nagyon fontos bemutatni.

Ez mutatja meg:

A Dataform valójában milyen SQL-t küld BigQuery felé.

---

# Workflow Configuration

Ez lesz az egyik leggyakrabban használt objektum.

---

## Mi a szerepe?

A Workflow Configuration határozza meg:

- mit futtatunk
- mikor futtatjuk
- milyen beállításokkal futtatjuk

---

## Mit mutassunk?

Workflow Configurations

---

Példák:

```text
daily_gold_refresh
```

```text
hourly_stage_refresh
```

---

# Mit lehet kiválasztani?

## Mely modellek fussanak?

Például:

```text
gold_sales
```

vagy

```text
gold/*
```

---

## Include dependencies

Ha bekapcsoljuk:

```text
gold_sales
```

futtatásakor előtte:

```text
int_sales
```

és

```text
stg_sales
```

is lefut.

---

## Include dependents

Fordított irány.

Ha futtatom:

```text
stg_sales
```

akkor az összes downstream modell is futhat.

---

Ez nagyon hasznos fejlesztés során.

---

# Full Refresh

Ez az egyik legfontosabb futtatási opció.

---

Normál esetben:

Incremental modell

↓

csak új rekordok

---

Full Refresh esetén:

Incremental modell

↓

teljes újraépítés

---

## Mikor használjuk?

Például:

- logika változott
- hibás adat került be
- új oszlop jelent meg
- új szabályt vezettünk be

---

## Mire figyeljünk?

Nagy tábláknál drága lehet.

Akár több száz GB vagy TB adatot is újraszámolhat.

---

# Execute gomb

## Mi történik?

Dataform:

1. dependency graph építés
2. compilation
3. BigQuery execution

---

## Mit mutassunk?

Execute

↓

Execution Details

---

# Execution Graph

Ez az egyik leghasznosabb debug eszköz.

---

Mutassuk meg:

```text
stg_sales
```

↓

```text
int_sales
```

↓

```text
gold_sales
```

---

Futás közben látszik:

- pending
- running
- success
- failed

---

# Mi történik hiba esetén?

Példa:

```text
int_sales
```

hiba.

---

Eredmény:

```text
stg_sales
```

sikeres

```text
int_sales
```

failed

```text
gold_sales
```

nem fut

---

Miért?

Mert a függőségi lánc megszakad.

---

Ez pontosan ugyanaz az elv mint Airflow DAG-oknál.

---

# Logok

## Mit mutassunk?

Execution

↓

Logs

---

Itt látható:

- BigQuery error
- SQL syntax error
- permission error
- assertion failure

---

Nagyon fontos.

A hibakeresés elsődleges helye.

---

# Assertions részletesen

A Dataform assertion valójában egy külön SQL ellenőrzés.

---

Példa:

```text
DealerCode NOT NULL
```

---

A Dataform generál egy ellenőrző queryt.

---

Ha talál hibás rekordot:

Execution

↓

Failed

---

A pipeline megáll.

---

## Miért jó?

A hibák nem jutnak el:

- GOLD rétegbe
- Power BI-ba
- Excel exportba

---

Már a pipeline szintjén megállnak.

---

# Javasolt repository struktúra

```text
definitions/

├── stage/
│
├── intermediate/
│
├── gold/
│
└── assertions/
```

---

## Miért?

A modellek és az adatminőség szétválik.

Ez nagyobb projektekben jelentősen javítja az átláthatóságot.

---

# Hogyan néz ki a teljes életciklus?

```text
Developer

↓

Workspace

↓

Commit

↓

Git

↓

Release Configuration

↓

Compilation Result

↓

Workflow Configuration

↓

Execution

↓

BigQuery

↓

Gold Layer

↓

Power BI
```
---

Ha ezt a folyamatot megértjük, akkor gyakorlatilag a Dataform teljes működési modelljét megértettük.