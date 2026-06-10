# Day 2 – Dataform Deep Dive

## Cél

Ebben a blokkban nem azt szeretnénk megtanulni, hogy melyik gombra kell kattintani a Dataform felületén.

A cél az, hogy megértsük:

- milyen problémát old meg a Dataform,
- hogyan kapcsolódik a BigQuery-höz,
- mi történik a háttérben egy futtatás során,
- hogyan épülnek fel a függőségek,
- hogyan lesz egy Alteryx workflow-ból Dataform pipeline,
- és miért választottuk ezt az eszközt a projektben.

A blokk végére világossá kell válnia, hogy a Dataform nem egy új adattárház és nem egy ETL motor. A Dataform egy olyan réteg a BigQuery fölött, amely segít nagy mennyiségű SQL modell szervezésében, verziókezelésében és futtatásában.

---

# Mi a Dataform valójában?

Az egyik leggyakoribb félreértés, hogy a Dataformot sokan ETL eszközként vagy adatfeldolgozó motorként képzelik el.

Valójában nem ez történik.

A Dataform:

- SQL build tool
- dependency manager
- orchestration layer
- analytics engineering eszköz

BigQuery fölött.

A tényleges adatfeldolgozást mindig a BigQuery végzi.

Nagyon fontos mondat:

> A Dataform nem dolgozza fel az adatot.
>
> A Dataform SQL-t generál.
>
> A BigQuery hajtja végre a SQL-t.

Ha ezt megértjük, akkor a Dataform működésének jelentős része már érthetővé válik.

---

# Miért nem elég a sima SQL?

Tegyük fel, hogy van három SQL lekérdezésünk.

```sql
sales_clean.sql
```

```sql
dealer_clean.sql
```

```sql
sales_report.sql
```

Ez még könnyen kezelhető.

Most képzeljük el ugyanezt egy valós vállalati adattárházban:

- 120 SQL modell
- 15 fejlesztő
- több ország
- több üzleti terület
- több környezet

Itt már nem az SQL megírása a nehéz.

A problémák:

- mi mire épül?
- milyen sorrendben fusson?
- mi történik ha módosítok egy modellt?
- hogyan verziózom?
- hogyan tesztelem?
- hogyan dokumentálom?

A Dataform pontosan ezekre a problémákra ad megoldást.

---

# Hol helyezkedik el a Dataform az architektúrában?

A mi architektúránkban:

```text
Cloud Storage
        ↓
      RAW
        ↓
    BigQuery
        ↓
    Dataform
        ↓
     STAGE
        ↓
 INTERMEDIATE
        ↓
      GOLD
        ↓
    Power BI
```

A Dataform nem váltja ki a BigQuery-t.

A BigQuery az adattárház.

A Dataform az a réteg, amely segít felépíteni az adattárházi objektumokat.

---

# Dataform Repository

A Dataform projekt alapegysége a Repository.

Technikailag ez egy Git repository.

Ebben található:

- SQLX modellek
- konfigurációk
- assertionök
- dokumentáció
- workflow beállítások

Aki Alteryx világából érkezik, annak ez az egyik legnagyobb szemléletváltás.

Az Alteryx-ben a logika egy workflow fájlban él.

Dataformban a logika szöveges fájlokban él.

Ez elsőre kevésbé látványos, viszont sokkal jobban verziókezelhető és karbantartható.

---

# Egy tipikus repository felépítése

Például:

```text
definitions/

├── stage
│   ├── stg_sales.sqlx
│   ├── stg_dealer.sqlx
│
├── intermediate
│   ├── int_sales_enriched.sqlx
│
└── gold
    ├── gold_sales_report.sqlx
```

Ez gyakorlatilag az adattárházi rétegek leképezése.

A cél az, hogy a repository struktúrája tükrözze az adattárház struktúráját.

---

# SQLX fájl felépítése

Vegyünk egy egyszerű példát.

```sql
config {
  type: "table",
  schema: "stage"
}

SELECT
    DealerCode,
    UPPER(Market) AS Market
FROM ${ref("raw_sales")}
```

Első ránézésre SQL-nek tűnik.

Valójában két külön részre bontható.

---

# A config blokk

```sql
config {
  type: "table",
  schema: "stage"
}
```

Ez nem SQL.

Ez Dataform konfiguráció.

A Dataform ebből tudja meg:

- milyen objektumot hozzon létre,
- melyik datasetbe kerüljön,
- milyen néven jelenjen meg,
- milyen futtatási szabályok vonatkozzanak rá.

Tulajdonképpen ez a modell metaadata.

---

# A SQL rész

```sql
SELECT
    DealerCode,
    UPPER(Market) AS Market
FROM ${ref("raw_sales")}
```

Ez már teljesen normál BigQuery SQL.

Ez fontos felismerés.

A Dataform nem próbál új SQL nyelvet kitalálni.

Ha valaki tud BigQuery SQL-t írni, akkor a Dataform nagy részét már érti.

---

# Mi az a ref()?

A Dataform egyik legfontosabb fogalma.

Példa:

```sql
SELECT *
FROM ${ref("stg_sales")}
```

A legtöbb kezdő kérdése:

Miért nem ezt írjuk?

```sql
project.stage.stg_sales
```

A válasz:

Mert a ref() sokkal többet csinál.

---

# Mit csinál a ref()?

A ref() három feladatot lát el egyszerre.

## 1. Objektumfeloldás

A Dataform automatikusan behelyettesíti a megfelelő projekt-, dataset- és táblanevet.

A fejlesztőnek nem kell hardcodeolnia.

---

## 2. Függőség létrehozása

A Dataform tudni fogja, hogy:

```text
int_sales
```

függ

```text
stg_sales
```

modelltől.

---

## 3. Lineage építés

A Dataform képes megrajzolni az adat útját.

Ez lesz a lineage vagy dependency graph.

---

# Dependency Graph

Tegyük fel, hogy a következő modelljeink vannak:

```text
raw_sales
      ↓
stg_sales
      ↓
int_sales_enriched
      ↓
gold_sales_report
```

A Dataform ebből gráfot épít.

Technikailag:

- Node = modell
- Edge = függőség

Ez gyakorlatilag egy DAG.

Ugyanaz az alapelv, amit később az Airflow esetében is látni fogunk.

---

# Mi történik a Run gomb megnyomása után?

Sokan azt gondolják:

```text
Run
 ↓
SQL fut
```

Valójában jóval több történik.

---

## 1. Modellek beolvasása

A Dataform végigolvassa az összes SQLX fájlt.

---

## 2. Függőségi gráf építése

A ref() hivatkozások alapján felépíti a DAG-ot.

---

## 3. Topológiai rendezés

Kiszámolja:

- mi mire épül,
- milyen sorrendben kell futtatni.

Például:

```text
stg_sales
↓
int_sales
↓
gold_sales
```

---

## 4. Compilation

A SQLX modellekből normál BigQuery SQL generálódik.

---

## 5. SQL küldése BigQuery felé

A Dataform API hívásokon keresztül elküldi a generált SQL-t.

---

## 6. BigQuery végrehajtás

Az adatfeldolgozást a BigQuery végzi.

A Dataform ebben a lépésben már csak koordinál.

---

# Compilation

Ez a Dataform egyik legfontosabb belső folyamata.

Vegyük ezt:

```sql
SELECT *
FROM ${ref("stg_sales")}
```

A Dataform ezt lefordítja valami ilyesmire:

```sql
SELECT *
FROM training_project.sales_stage.stg_sales
```

A BigQuery már ezt a SQL-t kapja meg.

Soha nem találkozik a ref() függvénnyel.

Ez kizárólag Dataform fogalom.

Ezért szoktuk azt mondani, hogy a Dataform tulajdonképpen egy SQL fordító.

---

# Table, View és Incremental modellek

A Dataform több objektumtípust támogat.

---

## Table

```sql
config {
  type: "table"
}
```

A modell minden futáskor teljesen újraépül.

Egyszerű és könnyen érthető.

---

## View

```sql
config {
  type: "view"
}
```

Nem tárol adatot.

Egy mentett SQL lekérdezést hoz létre.

---

## Incremental

```sql
config {
  type: "incremental"
}
```

Csak az új rekordokat dolgozza fel.

Nagy adattömegnél ez kritikus fontosságú.

---

# Miért fontos az Incremental?

Tegyük fel, hogy:

```text
Sales tábla
500 millió rekord
```

Nem szeretnénk minden nap újraszámolni az egészet.

Az Incremental modell csak az új adatokat dolgozza fel.

Ez:

- gyorsabb,
- olcsóbb,
- skálázhatóbb.

Nagyvállalati környezetben ez szinte kötelező technika.

---

# Assertions

A Dataform beépített adatminőség-ellenőrzése.

Például:

```text
DealerCode
```

nem lehet NULL.

vagy

```text
DealerCode
```

egyedi kell legyen.

Az assertionök külön SQL ellenőrzésekké fordulnak.

Ha a szabály sérül:

- a pipeline hibára fut,
- a probléma azonnal látható lesz.

Fontos alapelv:

> Nem a Power BI riportban akarjuk megtudni, hogy hibás az adat.
>
> A pipeline futásakor akarjuk megtudni.

---

# Dataform és Git

A Dataform teljesen Git-alapú.

Ez jelentős különbség az Alteryx-hez képest.

Minden változás:

- commitolható,
- reviewzható,
- visszagörgethető,
- dokumentálható.

Ez különösen fontos akkor, amikor több fejlesztő dolgozik ugyanazon az adattárházon.

---

# Dataform és az Alteryx workflow

Vegyük a korábban elemzett workflow-t.

Alteryx:

```text
Excel Mapping
       ↓
     Join
       ↓
    Filter
       ↓
   Formula
       ↓
 Summarize
       ↓
    Output
```

Dataform:

```text
stg_mapping
stg_sales
stg_dealer

        ↓

int_sales_enriched

        ↓

gold_mli_report
```

A logika nem változik.

Az eszköz változik.

---

# Miért ezt választottuk?

A dbt és a Dataform nagyon hasonló problémát old meg.

Ebben a projektben:

- BigQuery a célplatform,
- Composer lesz az orchestrator,
- Cloud Run kezeli a fájlokat.

Ebben a környezetben a Dataform natívan illeszkedik a GCP ökoszisztémába.

Kevesebb komponens.

Kevesebb üzemeltetés.

Egyszerűbb architektúra.

Ezért választottuk a Dataformot az Alteryx workflow-k migrációjához.