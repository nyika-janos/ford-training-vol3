ALTER TABLE `ford-training-430008.training_config.file_ingestion_run_log`
ADD COLUMN IF NOT EXISTS object_generation STRING
OPTIONS(description="A Cloud Storage objektum generációs azonosítója, amely segít ugyanazon fájlfeltöltés ismételt kézbesítésének kiszűrésében.");
