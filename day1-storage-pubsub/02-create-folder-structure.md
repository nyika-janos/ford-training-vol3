# 1. nap - 2. gyakorlat

# A Landing Zone structure létrehozása

## Cél

Hozz létre egy egyszerű, enterprise-style Landing Zone structure-t.

---

## Becsült idő

5 perc

---

## Háttér

A Cloud Storage egy object store.

A folderek hagyományos directoryk helyett logical prefixek.

Ennek ellenére a legtöbb organization standard structure-t használ az érkező, feldolgozott és exportált fájlok elkülönítésére.

---

## Target structure

```
landing/
archive/
error/
export/
```

---

## Lépések

### 1. lépés

Nyisd meg a bucketedet.

---

### 2. lépés

Hozd létre ezt a foldert:

```
landing/
```

---

### 3. lépés

Hozd létre ezt a foldert:

```
archive/
```

---

### 4. lépés

Hozd létre ezt a foldert:

```
error/
```

---

### 5. lépés

Hozd létre ezt a foldert:

```
export/
```

---

## Ellenőrzés

Ellenőrizd, hogy mind a négy folder látható-e.

```
landing/
archive/
error/
export/
```

---

## Megbeszélés

Hová helyeznéd az alábbiakat?

- Beérkező Excel-fájlok
- Sikeresen feldolgozott fájlok
- Érvénytelen fájlok
- Generált reportok
