# 1. nap - 1. gyakorlat

# Saját Cloud Storage bucket létrehozása

## Cél

Hozz létre egy saját Cloud Storage bucketet, amelyet a teljes training során használni fogsz.

A gyakorlat végére:

- Létrehozol egy Cloud Storage bucketet
- Kiválasztod a megfelelő regiont
- Kiválasztod a megfelelő storage classt
- Megérted a Cloud Storage szerepét a target architecture-ben

---

## Becsült idő

10 perc

---

## Előfeltételek

Hozzáféréssel rendelkezel az alábbihoz:

Project:

```
ford-training-430008
```

---

## Háttér

A target architecture-ben a Cloud Storage szolgál az érkező fájlok landing zone-jaként.

Tipikus példák:

- Excel mapping fájlok
- Classification fájlok
- Manuális business uploadok
- Exportált reportok

A platformra érkező összes fájl először a Cloud Storage-ba kerül.

---

## Lépések

### 1. lépés

Nyisd meg:

```
Cloud Storage
```

a Google Cloud Console-ból.

---

### 2. lépés

Kattints erre:

```
Create Bucket
```

---

### 3. lépés

Használd az alábbi naming conventiont:

```
training-<firstname>
```

Példák:

```
training-janos
training-peter
training-barni
```

A bucketneveknek globálisan egyedinek kell lenniük.

Ha a név már létezik, egészítsd ki egy véletlenszerű számmal.

Példa:

```
training-janos-001
```

---

### 4. lépés

Region:

Válaszd ki:

```
europe-west4
```

(Hollandia)

---

### 5. lépés

Storage Class:

Válaszd ki:

```
Standard
```

---

### 6. lépés

Az összes többi settinget hagyd default értéken.

Kattints erre:

```
Create
```

---

## Ellenőrzés

Ellenőrizd, hogy:

- A bucketed létezik
- A bucket megjelenik a Cloud Storage-ban
- A location `europe-west4`
- A storage class `Standard`

---

## Megbeszélés

Kérdés:

Miért a Cloud Storage a target architecture első componentje?

Gondolj az elemzett Alteryx workflow-kban használt Excel-fájlokra.
