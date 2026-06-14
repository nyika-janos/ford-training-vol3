# 1. nap - 6. gyakorlat

# A Cloud Storage összekapcsolása a Pub/Subbal

## Cél

Hozz létre egy Cloud Storage notificationt, amely Pub/Sub message-et publikál, amikor új fájlt töltenek fel a bucket **landing** folderébe.

A gyakorlat végére az alábbi flow fog működni:

```text
Excel
   ↓
Cloud Storage (landing/)
   ↓
Pub/Sub Topic
   ↓
Subscription
   ↓
Message
```

---

## Becsült idő

15 perc

---

## Háttér

A Cloud Storage eventeket generálhat, amikor valami történik egy bucketen belül.

Példák:

- Új fájl feltöltése
- Fájl törlése
- Object metadata frissítése

Ma az alábbi eventet használjuk:

```text
OBJECT_FINALIZE
```

Ez az event akkor következik be, amikor sikeresen létrejön egy új object a bucketben.

Korábban a notification configurationök közvetlenül a Cloud Storage user interface-ről is létrehozhatók voltak. Ma sok team a Google Cloud CLI-n keresztül kezeli őket.

A gyakorlat célja annak megértése, hogyan publikálható egy Cloud Storage által generált event a Pub/Subba.

Valós data platformokon általában nem generálunk eventet a bucket minden objectjéhez.

Ehelyett a notificationöket gyakran a storage hierarchy meghatározott területeire korlátozzuk.

Ebben a trainingben csak az ide érkező fájlokra szeretnénk reagálni:

```text
landing/
```

Az alábbi helyekre feltöltött fájlok:

```text
archive/
error/
export/
```

nem triggerelhetnek új ingestion processt.

Ez egy gyakori enterprise data platform design patternt tükröz.

További dokumentáció:

Cloud Storage Pub/Sub Notifications:

https://docs.cloud.google.com/storage/docs/pubsub-notifications

gcloud notification commands:

https://docs.cloud.google.com/sdk/gcloud/reference/storage/buckets/notifications

---

## 1. lépés

Nyisd meg a Cloud Shellt a Google Cloud Console-ból.

Várd meg, amíg a shell használatra kész.

---

## 2. lépés

Azonosítsd az erőforrásaidat.

### Bucket Name

Példa:

```text
training-janos
```

### Topic Name

```text
file-arrived-topic-<firstname>
```

---

## 3. lépés

Hozd létre a notification configurationt.

Cseréld le ezt:

```text
A_TE_BUCKET_NEVED
```

a bucketed nevére.

Cseréld le ezt:

```text
A_TE_PUB_SUB_TOPIC_NEVED
```

a topicod nevére.

Futtasd:

```bash
gcloud storage buckets notifications create gs://A_TE_BUCKET_NEVED \
  --topic=A_TE_PUB_SUB_TOPIC_NEVED \
  --event-types=OBJECT_FINALIZE \
  --object-prefix=landing/
```

Példa:

```bash
gcloud storage buckets notifications create gs://training-janos \
  --topic=file-arrived-topic-janos \
  --event-types=OBJECT_FINALIZE \
  --object-prefix=landing/
```

A további parameter:

```text
--object-prefix=landing/
```

biztosítja, hogy csak a landing folderbe feltöltött objectekhez generálódjanak notificationök.

A bucket más részeire feltöltött fájlok nem generálnak eventeket.

Várt output:

```text
Created notification config ...
```

---

## 4. lépés

Ellenőrizd a notification configurationt.

Futtasd:

```bash
gcloud storage buckets notifications list gs://A_TE_BUCKET_NEVED
```

Példa:

```bash
gcloud storage buckets notifications list gs://training-janos
```

Legalább egy notification configurationt kell látnod.

Példa:

```text
ID    Topic
1     projects/ford-training-430008/topics/file-arrived-topic-<firstname>
```

---

## 5. lépés

Tekintsd át a dokumentációt.

Nyisd meg a hivatalos dokumentációt:

https://docs.cloud.google.com/sdk/gcloud/reference/storage/buckets/notifications

Figyeld meg az elérhető parancsokat:

```bash
gcloud storage buckets notifications create
gcloud storage buckets notifications list
gcloud storage buckets notifications delete
```

Ezekkel a parancsokkal notification configurationöket hozhatsz létre, vizsgálhatsz meg és törölhetsz.

Áttekintheted a támogatott event type-okat és notification concepteket is:

https://docs.cloud.google.com/storage/docs/pubsub-notifications

---

## 6. lépés

Teszteld a notificationt.

### A teszt - Landing folder

Navigálj ide:

```text
Cloud Storage
```

↓

```text
A bucketed
```

↓

```text
landing/
```

Tölts fel egy tetszőleges kis fájlt.

Példák:

```text
landing/test.xlsx
landing/dummy.xlsx
landing/sample.xlsx
```

Várt eredmény:

✅ Pub/Sub message-nek kell generálódnia.

---

### B teszt - Export folder

Navigálj ide:

```text
export/
```

Tölts fel egy tetszőleges kis fájlt.

Példák:

```text
export/test.xlsx
export/dummy.xlsx
```

Várt eredmény:

✅ Nem generálódhat Pub/Sub message.

Ez megerősíti, hogy a notification a landing zone-ra korlátozódik.

---

## 7. lépés

Olvasd el a generált Pub/Sub message-et.

Navigálj ide:

```text
Pub/Sub
```

↓

```text
Subscriptions
```

↓

```text
file-arrived-sub
```

↓

```text
Messages
```

↓

```text
Pull
```

Kattints erre:

```text
Pull
```

az elérhető message-ek lekéréséhez.

---

## Ellenőrzés

Ellenőrizd az alábbiakat:

### 1. scenario

Töltsd fel:

```text
landing/test.xlsx
```

Eredmény:

✅ A Pub/Sub message megérkezett

---

### 2. scenario

Töltsd fel:

```text
export/test.xlsx
```

Eredmény:

✅ Nem érkezett Pub/Sub message

---

A notification configuration tehát megfelelően az alábbira korlátozódik:

```text
landing/
```

---

## Sikerkritériumok

Most már az alábbi architecture működik:

```text
Excel
   ↓
Cloud Storage (landing/)
   ↓
Pub/Sub Topic
   ↓
Subscription
   ↓
Message
```

A file upload automatikusan eventet generál, és message-et publikál a Pub/Subba.

Csak a landing zone-ba érkező fájlok triggerelik az eventet.

---

## Mi következik?

Ma manuálisan vizsgáljuk meg a message-et.

A 3. napon ugyanez az event egy Cloud Run service-t triggerel.

A 4. napon ugyanez az event egy Composer / Airflow workflow-t triggerelhet.

Az event változatlan marad.

Csak a consumer változik.

```text
1. nap:
Bucket → Pub/Sub

3. nap:
Bucket → Pub/Sub → Cloud Run

4. nap:
Bucket → Pub/Sub → Composer DAG
```

---

## Fő tanulság

A cél nem egyszerűen message-ek generálása.

A cél az, hogy csak business-relevant eventekhez generáljunk message-eket.

Az architecture-ben a landing zone az újonnan érkező adatokat képviseli.

Ezért csak az ide érkező fájlok:

```text
landing/
```

triggerelhetnek downstream processinget.

Az alábbi helyekre tett fájlok:

```text
archive/
error/
export/
```

nem indíthatnak új ingestion processt.

Ugyanezt a design principle-t követjük később is, amikor a Cloud Run, a Dataform és a Composer bekerül az architecture-be.
