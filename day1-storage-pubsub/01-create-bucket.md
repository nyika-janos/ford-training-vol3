# Day 1 - Exercise 1

# Create Your Personal Cloud Storage Bucket

## Objective

Create a personal Cloud Storage bucket that will be used throughout the entire training.

By the end of this exercise you will:

- Create a Cloud Storage bucket
- Select an appropriate region (europe-west4)
- Select an appropriate storage class
- Understand the role of Cloud Storage in the target architecture

---

## Estimated Time

10 minutes

---

## Prerequisites

You have access to:

Project:

```
ford-training-430008
```

---

## Background

In the target architecture, Cloud Storage will serve as the landing zone for incoming files.

Typical examples:

- Excel mapping files
- Classification files
- Manual business uploads
- Exported reports

All files entering the platform will first arrive in Cloud Storage.

---

## Steps

### Step 1

Open:

```
Cloud Storage
```

from the Google Cloud Console.

---

### Step 2

Click:

```
Create Bucket
```

---

### Step 3

Use the following naming convention:

```
training-<firstname>
```

Examples:

```
training-janos
training-peter
training-barni
```

Bucket names must be globally unique.

If the name already exists, append a random number.

Example:

```
training-janos-001
```

---

### Step 4

Region:

Select:

```
europe-west4
```

(Netherlands)

---

### Step 5

Storage Class:

Select:

```
Standard
```

---

### Step 6

Leave all other settings as default.

Click:

```
Create
```

---

## Validation

Verify that:

- Your bucket exists
- The bucket appears in Cloud Storage
- The location is europe-west4
- The storage class is Standard

---

## Discussion

Question:

Why is Cloud Storage the first component in our target architecture?

Think about the Excel files used in the analyzed Alteryx workflows.