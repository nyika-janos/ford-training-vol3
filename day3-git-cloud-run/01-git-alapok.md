# 01 - Git alapok

## Cél

Ebben a blokkban nem GitHubbal kezdünk.

Először magát a Gitet szeretnénk megérteni.

A cél az, hogy világos legyen:

- mire való a Git,
- mit jelent a repository,
- mi az a commit,
- hogyan követi a Git a változásokat,
- mire való a branch,
- miért fontos ez Dataform és Cloud Run mellett.

A GitHub, GitLab és Bitbucket később jönnek.

Ezek nem maga a Git.

Ezek olyan szolgáltatások, amelyek Git repositorykat tudnak tárolni és csapatmunkához kapcsolódó funkciókat adnak hozzá.

---

# Miért beszélünk Gitről ezen a tréningen?

A korábbi Alteryx világban sokszor egy workflow fájlban élt a logika.

Például:

```text
sales_workflow.yxmd
```

Ezt a fájlt valaki módosította, elmentette, elküldte, vagy feltöltötte egy közös helyre.

Ez működhet kis méretben.

Nagyobb csapatban viszont gyorsan felmerülnek kérdések:

- Ki módosította?
- Mit módosított?
- Mikor módosította?
- Miért módosította?
- Vissza tudunk térni egy korábbi állapothoz?
- Ketten dolgozhatnak ugyanazon a logikán egyszerre?

A Git ezekre a kérdésekre ad választ.

Dataformban azért fontos, mert a modellek fájlokban élnek:

- SQLX fájlokban,
- konfigurációkban,
- workflow beállításokban,
- dokumentációban.

Cloud Run esetében pedig a futtatott logika általában kódban él:

- Python fájlokban,
- konfigurációs fájlokban,
- dependency leírásokban,
- deployment beállításokban.

Ha a logika fájlokban él, akkor szükségünk van egy megbízható módszerre a változások követésére.

Ez a Git.

---

# Mi a Git?

A Git egy verziókezelő rendszer.

Egyszerűbben:

> A Git emlékszik arra, hogyan változtak a fájlok az időben.

Nem csak az aktuális állapotot látjuk.

Látjuk az előzményeket is.

Például:

```text
Hétfő:
sales_report.sqlx létrejött

Kedd:
hozzáadtuk a dealer adatokat

Szerda:
javítottunk egy hibás szűrést

Csütörtök:
visszaálltunk a szerdai verzióra
```

A Git nem csak mentés.

A Git strukturált történet.

---

# Mi az a repository?

A repository egy Git által kezelt projektmappa.

Röviden gyakran így mondjuk:

```text
repo
```

Egy repository tartalmazza:

- a projekt fájljait,
- a változások történetét,
- a brancheket,
- a commitokat,
- a Git saját belső metaadatait.

Példa Dataform projektre:

```text
training_dataform_repo
├── definitions
│   ├── stage
│   ├── intermediate
│   └── gold
├── includes
└── workflow_settings.yaml
```

Példa Cloud Run projektre:

```text
cloud-run-importer
├── main.py
├── requirements.txt
├── Dockerfile
└── README.md
```

A Git szempontjából mindkettő ugyanaz:

fájlokból álló projekt, amelynek követni szeretnénk a változásait.

---

# Git nem ugyanaz, mint GitHub

Ez nagyon fontos.

## Git

A Git maga a verziókezelő eszköz.

Futhat a saját gépünkön.

Nem kell hozzá GitHub.

Nem kell hozzá internet.

Egy lokális mappában is tudjuk használni.

## GitHub

A GitHub egy online szolgáltatás Git repositoryk tárolására.

Hasonló szolgáltatások:

- GitLab
- Bitbucket
- Azure Repos

Ezek adnak plusz funkciókat:

- webes felület,
- pull request,
- jogosultságkezelés,
- review folyamat,
- issue tracking,
- CI/CD integráció.

De az alap továbbra is a Git.

Először ezt kell megérteni.

---

# A Git három fontos állapota

Amikor dolgozunk egy repositoryban, a fájlok több állapotban lehetnek.

## Working directory

Ez az aktuális munkamappa.

Itt szerkesztjük a fájlokat.

Például módosítunk egy SQLX fájlt vagy egy Python scriptet.

## Staging area

Ez az előkészítő terület.

Itt mondjuk meg a Gitnek:

> Ezeket a változásokat szeretném a következő mentési pontba betenni.

## Repository history

Ez a commitok története.

Ide kerülnek a véglegesített változások.

Egyszerűen:

```text
Working directory
       ↓
   Staging area
       ↓
     Commit
       ↓
 Repository history
```

---

# Mi az a commit?

A commit egy mentési pont.

De nem olyan mentés, mint amikor megnyomjuk a `Save` gombot.

A commitnak jelentése van.

Egy jó commit:

- egy logikai változást tartalmaz,
- röviden leírja, mi történt,
- visszakereshető,
- összehasonlítható más commitokkal,
- szükség esetén visszavonható.

Példa commit üzenetek:

```text
Add raw sales table definition
```

```text
Fix dealer join in gold sales report
```

```text
Add Cloud Run importer configuration
```

Nem ideális commit üzenetek:

```text
changes
```

```text
fix
```

```text
asdf
```

A commit üzenet később másoknak, és a jövőbeli önmagunknak is segít.

---

# Mit lát a Git?

A Git fájlváltozásokat lát.

Például:

- új fájl jött létre,
- egy fájl módosult,
- egy fájl törölve lett,
- egy sor bekerült,
- egy sor kikerült.

Ezt nevezzük diffnek.

Példa:

```diff
- WHERE market = "HU"
+ WHERE market IN ("HU", "CZ", "SK")
```

Ez sokkal pontosabb, mint annyit tudni, hogy:

```text
sales_report.sqlx módosult
```

A Git meg tudja mutatni, pontosan mi változott.

---

# Alap parancsok

Ezeket nem kell azonnal fejből tudni.

Most az a fontos, hogy értsük, mit jelentenek.

## Repository létrehozása

```bash
git init
```

Ez azt mondja:

> Ezt a mappát mostantól Git repositoryként szeretném kezelni.

## Állapot lekérdezése

```bash
git status
```

Ez megmutatja:

- mely fájlok változtak,
- mi van staging area-ban,
- mi nincs még commitolva.

## Változás előkészítése

```bash
git add README.md
```

Ez beteszi a változást a staging area-ba.

## Commit készítése

```bash
git commit -m "Add project overview"
```

Ez létrehoz egy új mentési pontot.

## Előzmények megtekintése

```bash
git log
```

Ez megmutatja a commit történetet.

## Különbségek megtekintése

```bash
git diff
```

Ez megmutatja, mi változott a fájlokban.

---

# Mi az a branch?

A branch egy külön fejlesztési irány.

Képzeljük el úgy, mint egy párhuzamos munkaszálat.

Van egy fő vonal:

```text
main
```

Ezen van a stabil állapot.

Ha új dolgon dolgozunk, létrehozhatunk egy új branchet:

```text
feature/add-cloud-run-importer
```

Így az új munka nem keveredik azonnal a stabil állapottal.

Egyszerű kép:

```text
main:      A --- B --- C
                 \
feature:          D --- E
```

A `D` és `E` commitok egy külön ágon készülnek.

Ha elkészültek, vissza lehet őket vezetni a fő ágba.

---

# Miért jó a branch?

Branch használatával:

- több ember dolgozhat párhuzamosan,
- kipróbálhatunk változtatásokat,
- elkülöníthetjük a félkész munkát,
- review előtt nem rontjuk el a stabil verziót,
- Dataformban és Cloud Runban is kontrolláltabban kezeljük a változásokat.

Példa:

```text
main
feature/add-stage-models
feature/fix-gold-sales
feature/add-cloud-run-export
```

---

# Mi az a merge?

A merge azt jelenti, hogy egy branch változásait visszavezetjük egy másik branchbe.

Például:

```text
feature/add-cloud-run-importer
```

elkészült, teszteltük, jó.

Ezután bekerülhet:

```text
main
```

A merge célja:

> A külön fejlesztett munka legyen része a közös stabil állapotnak.

---

# Mi az a conflict?

Conflict akkor történik, amikor a Git nem tudja automatikusan eldönteni, melyik változás legyen érvényes.

Példa:

Két ember ugyanannak a fájlnak ugyanazt a sorát módosítja.

Az egyik változat:

```sql
WHERE market = "HU"
```

A másik változat:

```sql
WHERE market IN ("HU", "CZ", "SK")
```

A Git ilyenkor nem dönt helyettünk.

Megáll, és azt mondja:

> Ezt embernek kell eldöntenie.

Ez nem hiba.

Ez a Git egyik biztonsági mechanizmusa.

---

# Hogyan kapcsolódik ez Dataformhoz?

Dataformban a repository tartalmazza az adattranszformációs logikát.

Például:

```text
definitions/stage/stg_sales.sqlx
definitions/intermediate/int_sales_enriched.sqlx
definitions/gold/gold_sales_report.sqlx
workflow_settings.yaml
```

Ha valaki módosítja a `gold_sales_report.sqlx` fájlt, a Git meg tudja mutatni:

- melyik sor változott,
- ki változtatta,
- mikor változott,
- melyik commitban változott,
- visszaállítható-e egy korábbi verzió.

Ezért fontos, hogy Dataform mellett értsük a Git alapjait.

---

# Hogyan kapcsolódik ez Cloud Runhoz?

Cloud Run esetében gyakran alkalmazáskódot deployolunk.

Például egy Python service-t:

```text
main.py
requirements.txt
Dockerfile
```

Ez a kód mondhatja meg:

- hogyan olvassunk Cloud Storage-ból,
- hogyan dolgozzunk fel egy Pub/Sub üzenetet,
- hogyan töltsünk adatot BigQuery-be,
- hogyan exportáljunk adatot Excelbe.

Ha ez a kód változik, ugyanazok a kérdések merülnek fel:

- mi változott?
- ki változtatta?
- működött-e az előző verzió?
- vissza tudunk-e állni?
- melyik verzió lett deployolva?

A Git itt is a változások történetét adja.

---

# Fontos szemlélet

A Git nem csak fejlesztőknek való.

Mindenkinek hasznos, aki üzleti logikát, SQL-t, konfigurációt vagy adatfeldolgozási szabályokat módosít.

Az Alteryx workflow-oknál sokszor a vizuális felület adta a biztonságérzetet.

Cloud környezetben a biztonságot részben az adja, hogy:

- a logika fájlokban van,
- a fájlok verziózva vannak,
- a változások visszakereshetők,
- a módosítások review-zhatók,
- a deployment kontrollált.

Ezért nem a GitHubbal kezdünk.

Először azt értjük meg, hogy maga a Git hogyan gondolkodik a változásokról.

---

# Rövid összefoglaló

A Git:

- verziókezelő rendszer,
- repositorykban gondolkodik,
- commitokkal rögzíti a változásokat,
- diffként mutatja meg, mi módosult,
- branchekkel támogatja a párhuzamos munkát,
- merge segítségével egyesíti a változásokat,
- conflict esetén emberi döntést kér.

A GitHub, GitLab és Bitbucket erre épülő online szolgáltatások.

Dataform és Cloud Run mellett azért fontos a Git, mert mindkét esetben fájlokban él a logika, és ezeknek a változásait kontrolláltan kell kezelni.
