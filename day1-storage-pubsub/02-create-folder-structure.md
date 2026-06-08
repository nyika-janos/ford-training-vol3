# Day 1 - Exercise 2

# Create the Landing Zone Structure

## Objective

Create a basic enterprise-style landing zone structure.

---

## Estimated Time

5 minutes

---

## Background

Cloud Storage is an object store.

Folders are logical prefixes rather than traditional directories.

Even so, most organizations use a standard structure to separate incoming, processed and exported files.

---

## Target Structure

```
landing/
archive/
error/
export/
```

---

## Steps

### Step 1

Open your bucket.

---

### Step 2

Create folder:

```
landing/
```

---

### Step 3

Create folder:

```
archive/
```

---

### Step 4

Create folder:

```
error/
```

---

### Step 5

Create folder:

```
export/
```

---

## Validation

Verify that all four folders are visible.

```
landing/
archive/
error/
export/
```

---

## Discussion

Where would you place:

- Incoming Excel files?
- Successfully processed files?
- Invalid files?
- Generated reports?