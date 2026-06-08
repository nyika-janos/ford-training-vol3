# Day 1 - Exercise 6

# Connect Cloud Storage to Pub/Sub

## Objective

Generate Pub/Sub messages whenever a new file is uploaded.

---

## Estimated Time

15 minutes

---

## Steps

### Step 1

Open your bucket.

---

### Step 2

Navigate to:

```
Notifications
```

---

### Step 3

Create notification.

Event type:

```
Object Finalize
```

This event occurs when a new file is successfully created.

---

### Step 4

Destination:

```
Pub/Sub
```

---

### Step 5

Select topic:

```
file-arrived-topic
```

---

### Step 6

Save.

---

## Test

Upload a file:

```
landing/test.xlsx
```

or any small Excel file.

---

## Read the Message

Open:

```
Pub/Sub
```

↓

```
Subscriptions
```

↓

```
file-arrived-sub
```

↓

```
Pull Messages
```

---

## Validation

Verify that a message appears.

Review the payload.

Look for:

- Bucket name
- Object name
- Event type
- Timestamp

---

## Success Criteria

The following flow is working:

```
Excel
   ↓
Cloud Storage
   ↓
Pub/Sub
   ↓
Message
```

---

## What Happens Next?

Day 2:

```
Excel
   ↓
Cloud Storage
   ↓
Pub/Sub
   ↓
BigQuery
```

Day 3:

```
Excel
   ↓
Cloud Storage
   ↓
Pub/Sub
   ↓
Cloud Run
```

Day 4:

```
Excel
   ↓
Cloud Storage
   ↓
Pub/Sub
   ↓
Composer DAG
```