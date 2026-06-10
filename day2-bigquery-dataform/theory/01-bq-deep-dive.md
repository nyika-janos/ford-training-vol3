# Day 2 - BigQuery Deep Dive

## Cél

Ez a blokk nem a BigQuery összes funkciójának bemutatásáról szól.

A cél az, hogy megértsük:

- Mi a BigQuery szerepe a célarchitektúrában?
- Miért adattárház és nem adatbázis?
- Hogyan szervezzük az adatokat?
- Milyen költség- és teljesítménybeli szempontokra kell figyelni?
- Hogyan kapcsolódik a Dataformhoz és az Alteryx migrációhoz?

---

# 1. BigQuery Studio

## Mit mutassunk?

- BigQuery Studio
- Explorer panel
- Query Editor
- Job History

## Beszéljünk róla

A BigQuery Studio lesz az egyik leggyakrabban használt felületünk.

Tegnap az adat beérkezésével foglalkoztunk. Ma onnan folytatjuk, hogy az adat már bent van a platformon.

A BigQuery lesz az a központi hely, ahol:

- tároljuk az adatokat,
- SQL lekérdezéseket futtatunk,
- adattárházi rétegeket építünk,
- és amelyre később a Dataform is épül.

A GCP-s adatplatform szívének tekinthetjük.

---

# 2. BigQuery architektúra

## Kulcsszavak

- Serverless
- Managed Service
- Data Warehouse
- Elastic Scaling

## Beszéljünk róla

A BigQuery egyik legfontosabb tulajdonsága, hogy teljesen szervermentes szolgáltatás.

Nem telepítünk adatbázist.

Nem kezelünk VM-eket.

Nem konfigurálunk clustereket.

Nem foglalkozunk patch-eléssel vagy verziófrissítésekkel.

A Google üzemelteti az infrastruktúrát, mi pedig kizárólag az adatokkal és a lekérdezésekkel foglalkozunk.

### Kérdés a hallgatóknak

Mit kell átállítanunk, ha holnap tízszer akkora lesz az adattömeg?

A legtöbb esetben semmit.

Ez az egyik legnagyobb különbség a klasszikus adatbázisokhoz képest.

---

# 3. BigQuery objektumhierarchia

## Mutassuk meg

Project → Dataset → Table

## Beszéljünk róla

A BigQuery objektumai hierarchiába szerveződnek.

A legfelső szint a Project.

Ezen belül találhatók a Datasetek.

A Dataseteken belül pedig a Table, View és Materialized View objektumok.

### Egyszerű analógia

Windows:

Drive → Mappa → Fájl

BigQuery:

Project → Dataset → Table

---

# 4. Datasetek szerepe

## Mutassuk meg

- sales_raw
- sales_stage
- sales_gold

## Beszéljünk róla

A Dataset nem technikai kényszer.

Szervezési eszköz.

Segítségével:

- elkülöníthetők a rétegek,
- egyszerűbb a jogosultságkezelés,
- átláthatóbb az adattárház.

A tréning során rétegenként külön dataseteket használunk.

Ez jól láthatóvá teszi az adat útját.

---

# 5. Táblák

## Mutassuk meg

Egy konkrét tábla:

- Schema
- Preview
- Details

## Beszéljünk róla

A táblák fizikailag tárolják az adatot.

Fontos fogalmak:

- oszlopok
- adattípusok
- metaadatok
- rekordszám

Külön hangsúlyozzuk:

A BigQuery erősen támaszkodik a megfelelő adattípusokra.

Egy dátum STRING-ben tárolva nem valódi dátum.

A Stage réteg egyik fontos feladata ezek javítása.

---

# 6. SQL Query Editor

## Mutassuk meg

```sql
SELECT *
FROM sales_raw.sales
LIMIT 10;
```

## Beszéljünk róla

A BigQuery alapvetően SQL-alapú rendszer.

Minden transzformáció SQL-re épül.

A Dataform is SQL-t generál.

A Power BI is SQL-t küld.

A BigQuery ezért lesz a teljes adatplatform központi végrehajtó motorja.

---

# 7. Query History és Job History

## Mutassuk meg

Job History

## Beszéljünk róla

Minden futtatás naplózásra kerül.

Látható:

- ki futtatta,
- mikor futtatta,
- mennyi adatot olvasott,
- mennyi ideig futott.

Ez rendkívül fontos audit és költségkontroll szempontjából.

---

# 8. Költségmodell

## Mutassuk meg

Execution Details

Estimated Bytes

Dry Run

## Beszéljünk róla

A BigQuery költsége alapvetően két részből áll:

### Tárolás

Mennyi adatot tárolunk.

### Lekérdezés

Mennyi adatot olvasunk.

A kettő külön kezelendő.

Gyakran a rosszul megírt lekérdezések okozzák a nagyobb költséget.

---

# 9. Miért gyors a BigQuery?

## Kulcsszó

Columnar Storage

## Beszéljünk róla

A BigQuery nem sorokban tárolja az adatot.

Oszlopokban tárolja.

Ez lehetővé teszi, hogy csak azokat az oszlopokat olvassa be, amelyekre valóban szükség van.

Például:

```sql
SELECT SUM(SalesAmount)
FROM sales;
```

nem olvassa be az összes többi oszlopot.

Ez jelentősen csökkenti a feldolgozandó adatmennyiséget.

---

# 10. Partitioning

## Mutassuk meg

Table Details

Partitioning

## Beszéljünk róla

A partícionálás az adatok nagyobb logikai szeletekre bontását jelenti.

Leggyakrabban dátum alapján történik.

Példa:

2024-es adatok

2025-ös adatok

2026-os adatok

Ha csak tegnapi adatot kérünk le, akkor nem kell a teljes táblát végigolvasni.

Ez:

- gyorsabb,
- olcsóbb,
- hatékonyabb.

---

# 11. Clustering

## Mutassuk meg

Cluster Columns

## Beszéljünk róla

A clustering a partíción belüli rendezést segíti.

Tipikus kulcsok lehetnek:

- Market
- Country
- DealerCode

Ha a lekérdezések gyakran ezekre szűrnek, akkor a clustering tovább csökkentheti az olvasott adatmennyiséget.

---

# 12. Jogosultságkezelés

## Mutassuk meg

Dataset Permissions

## Beszéljünk róla

A BigQuery az IAM rendszert használja.

Nem minden felhasználónak kell minden réteget látnia.

Példa:

Power BI:

- sales_gold

Adatmérnök:

- sales_raw
- sales_stage
- sales_gold

A jogosultságokat általában csoportokon keresztül kezeljük.

---

# 13. Materialized View

## Beszéljünk róla

A hagyományos View minden alkalommal újrafuttatja a mögötte lévő SQL-t.

A Materialized View bizonyos eredményeket eltárol.

Ez gyorsabb válaszidőt eredményezhet gyakran használt aggregációk esetén.

Nem kötelező használni, de fontos ismerni a fogalmat.

---

# 14. Kapcsolat az Alteryx migrációval

## Beszéljünk róla

A BigQuery nem az Alteryx helyettesítője.

A BigQuery az új adattárház.

Az Alteryx workflow-k logikája később Dataform modellekbe kerül.

A BigQuery lesz az a motor, amely ezeket a modelleket végrehajtja.

A következő blokkban pontosan ezt fogjuk megnézni:

hogyan lesz egy Alteryx workflow-ból Dataform pipeline.