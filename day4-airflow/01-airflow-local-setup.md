# Lokális Airflow környezet létrehozása Dockerrel

Ez a rövid leírás azt mutatja be, hogyan hoztunk létre egy **lokális Apache Airflow környezetet Docker Compose segítségével**.  
A cél nem production környezet építése, hanem egy tréninghez, tanuláshoz és DAG-fejlesztéshez használható helyi Airflow setup.

A környezet tartalmazza az Airflow alapvető komponenseit:

- Airflow web UI
- scheduler
- worker
- metadata database
- lokális `dags`, `logs`, `plugins`, `config` mappák

A későbbi cél az, hogy ebből a lokális Airflow-ból GCP komponenseket hívjunk meg, például:

- Cloud Run Job importer
- Dataform workflow invocation
- Cloud Run Job exporter

---

## 1. Docker ellenőrzése

Először ellenőrizzük, hogy a Docker és a Docker Compose elérhető-e.

```bash
docker --version
docker compose version
```

Ha mindkét parancs verziószámot ad vissza, akkor a Docker alapvetően működik.

Példa:

```text
Docker version 28.x.x
Docker Compose version v2.x.x
```

---

## 2. Docker Desktop erőforrások

Airflow Docker Compose-zal több konténert indít, ezért érdemes ellenőrizni, hogy a Docker Desktop kapott-e elég memóriát.

Javasolt minimum:

```text
4 GB RAM
```

Kényelmesebb:

```text
6-8 GB RAM
```

### macOS

Docker Desktopban:

```text
Settings → Resources
```

Itt lehet ellenőrizni vagy módosítani a Dockernek adott memóriát.

### Windows

Docker Desktopban szintén:

```text
Settings → Resources
```

Windows esetén jellemzően WSL2 backend fut a Docker mögött. Ha a Docker furcsán viselkedik, érdemes ellenőrizni, hogy a WSL2 rendben működik-e.

---

## 3. Projektmappa létrehozása

Hozzunk létre egy külön mappát az Airflow környezetnek.

### macOS / Linux

```bash
mkdir -p ~/gcp-training-airflow
cd ~/gcp-training-airflow
```

### Windows PowerShell

Példa PowerShellben:

```powershell
mkdir $HOME\gcp-training-airflow
cd $HOME\gcp-training-airflow
```

Vagy tetszőleges munkamappában:

```powershell
mkdir gcp-training-airflow
cd gcp-training-airflow
```

---

## 4. Airflow mappák létrehozása

A lokális Airflow környezethez hozzuk létre a szükséges mappákat.

### macOS / Linux

```bash
mkdir -p dags logs plugins config
```

### Windows PowerShell

```powershell
mkdir dags, logs, plugins, config
```

A mappák szerepe:

| Mappa | Szerep |
|---|---|
| `dags` | Ide kerülnek az Airflow DAG Python fájlok |
| `logs` | Ide kerülnek a task futási logok |
| `plugins` | Saját Airflow pluginek helye, ha később kell |
| `config` | Konfigurációs fájlok helye |

---

## 5. Hivatalos Airflow docker-compose.yaml letöltése

A hivatalos Airflow Docker Compose fájlt használjuk.

### macOS / Linux

```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'
```

### Windows PowerShell

PowerShellben is működhet a `curl`, de Windows alatt ez gyakran alias. Biztosabb megoldás:

```powershell
Invoke-WebRequest -Uri "https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml" -OutFile "docker-compose.yaml"
```

Ellenőrzés:

```bash
ls
```

Windows PowerShellben:

```powershell
dir
```

A mappában meg kell jelennie ennek:

```text
docker-compose.yaml
```

---

## 6. `.env` fájl létrehozása

A `.env` fájlban adjuk meg az `AIRFLOW_UID` értéket. Ez főleg macOS/Linux alatt fontos, hogy a Docker által létrehozott fájlok jogosultsága rendben legyen.

### macOS / Linux

```bash
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

Ellenőrzés:

```bash
cat .env
```

Példa eredmény:

```text
AIRFLOW_UID=501
```

### Windows PowerShell

Windows alatt általában elég egy egyszerű értéket megadni:

```powershell
"AIRFLOW_UID=50000" | Out-File -Encoding ascii .env
```

Ellenőrzés:

```powershell
type .env
```

Példa eredmény:

```text
AIRFLOW_UID=50000
```

---

## 7. Airflow inicializálása

Az első indítás előtt inicializálni kell az Airflow környezetet.

```bash
docker compose up airflow-init
```

Ez létrehozza az Airflow metadata adatbázist, előkészíti a konténereket, és létrehozza az alapértelmezett felhasználót.

A belépési adatok a hivatalos quickstart setupban:

```text
username: airflow
password: airflow
```

Ha az inicializálás sikeres, a folyamat hiba nélkül lefut, és visszaadja a promptot.

---

## 8. Airflow indítása

Airflow indítása előtérben:

```bash
docker compose up
```

Ez első próbára hasznos, mert látjuk a konténerek logjait a terminálban.

Háttérben futtatás:

```bash
docker compose up -d
```

Ha a konténerek elindultak, az Airflow UI itt érhető el:

```text
http://localhost:8080
```

Belépés:

```text
airflow / airflow
```

---

## 9. Első teszt DAG létrehozása

Hozzunk létre egy egyszerű DAG-ot a `dags` mappában.

Fájl neve:

```text
dags/hello_training_dag.py
```

Tartalma:

```python
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="hello_training_dag",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["training"],
) as dag:

    hello = BashOperator(
        task_id="hello",
        bash_command="echo 'Szia Airflow, indul a negyedik tréningnap!'",
    )

    show_date = BashOperator(
        task_id="show_date",
        bash_command="date",
    )

    hello >> show_date
```

### macOS / Linux példa fájl létrehozásra

```bash
nano dags/hello_training_dag.py
```

### Windows

Windows alatt létrehozható például VS Code-dal:

```powershell
code dags\hello_training_dag.py
```

Vagy bármilyen szövegszerkesztővel.

---

## 10. DAG futtatása az Airflow UI-ból

Nyisd meg:

```text
http://localhost:8080
```

Lépések:

1. Keresd meg a `hello_training_dag` DAG-ot.
2. Ha szükséges, kapcsold be / unpause-old.
3. Kattints a **Trigger DAG** gombra.
4. Nyisd meg a DAG-ot.
5. Nézd meg a **Graph** vagy **Grid** nézetet.
6. Kattints a taskokra.
7. Nézd meg a task logokat.

A DAG két taskból áll:

```text
hello
  ↓
show_date
```

Ez azt mutatja meg, hogy az Airflow hogyan kezeli a taskokat, a függőségeket, a futási állapotokat és a logokat.

---

## 11. Hasznos Docker Compose parancsok

Konténerek állapotának ellenőrzése:

```bash
docker compose ps
```

Airflow leállítása:

```bash
docker compose down
```

Airflow újraindítása háttérben:

```bash
docker compose up -d
```

Logok követése:

```bash
docker compose logs -f
```

Csak a scheduler logjainak követése:

```bash
docker compose logs -f airflow-scheduler
```

Teljes törlés volume-okkal együtt:

```bash
docker compose down --volumes --remove-orphans
```

Figyelem: a `--volumes` törli az Airflow metadata adatbázis lokális volume-ját is, tehát a korábbi futások, állapotok és beállítások elvesznek.

---

## 12. macOS és Windows közötti fő különbségek

| Terület | macOS | Windows |
|---|---|---|
| Terminál | Terminal / iTerm / zsh | PowerShell / Windows Terminal |
| Mappa létrehozás | `mkdir -p` | `mkdir` vagy PowerShell több mappával |
| `.env` létrehozás | `echo -e "AIRFLOW_UID=$(id -u)" > .env` | `"AIRFLOW_UID=50000" | Out-File -Encoding ascii .env` |
| Compose fájl letöltése | `curl -LfO ...` | `Invoke-WebRequest ... -OutFile ...` |
| Docker backend | Docker Desktop | Docker Desktop + jellemzően WSL2 |
| Jogosultsági problémák | UID miatt lehet fontos a `.env` | WSL2 / fájlmegosztás okozhat eltérést |

---

## 13. Mit kaptunk ezzel?

Ezzel létrejött egy lokális Airflow környezet, amely alkalmas arra, hogy megmutassuk az Airflow alapjait:

- DAG
- task
- dependency
- manual trigger
- schedule
- success / failed állapot
- task log
- retry
- Graph view
- Grid view

Ezután a következő lépés az lehet, hogy a lokális Airflow DAG már nem csak teszt parancsokat futtat, hanem valódi GCP komponenseket hív:

```text
Lokális Airflow
   ↓
Cloud Run importer Job
   ↓
Dataform workflow invocation
   ↓
Cloud Run exporter Job
```

Ehhez később szükség lesz:

- Google provider csomagokra Airflow-ban
- GCP autentikációra
- megfelelő service accountra vagy application default credentials-re
- Cloud Run és Dataform jogosultságokra
- a pontos project ID, régió, job nevek és Dataform repository adatok megadására

---

## 14. Fontos megjegyzés

Ez a Docker Compose-os Airflow setup **lokális fejlesztésre és oktatásra jó**, nem production futtatásra.

Production környezetben jellemzően menedzselt vagy dedikált Airflow platformot használnak, például:

- Google Cloud Composer
- Astronomer
- saját Kubernetes alapú Airflow
- egyéb menedzselt Airflow szolgáltatások

A tréning céljára viszont ez a lokális setup tökéletes, mert ingyenes, gyorsan újraépíthető, és jól bemutatja az Airflow működésének lényegét.
