CREATE SCHEMA IF NOT EXISTS `ford-training-430008.training_config`
OPTIONS (
  location = "europe-west4"
);

CREATE TABLE IF NOT EXISTS `ford-training-430008.training_config.file_ingestion_config`
(
  config_id STRING NOT NULL OPTIONS(description="A betöltési szabály egyedi technikai azonosítója."),
  enabled BOOL NOT NULL OPTIONS(description="Azt jelzi, hogy az adott betöltési szabály aktív-e."),
  priority INT64 NOT NULL OPTIONS(description="A szabályok feldolgozási sorrendjét határozza meg, kisebb érték fut előbb."),
  file_pattern STRING NOT NULL OPTIONS(description="Reguláris kifejezés, amely eldönti, hogy a feltöltött fájlnév illeszkedik-e erre a szabályra."),
  source_format STRING NOT NULL OPTIONS(description="A forrásfájl formátuma, például CSV vagy XLSX."),
  sheet_name STRING OPTIONS(description="Excel forrás esetén annak a sheetnek a neve, amelyet be kell olvasni."),
  target_project STRING OPTIONS(description="A cél BigQuery projekt azonosítója; ha nincs megadva, az importer alapértelmezett projektje használható."),
  target_dataset STRING NOT NULL OPTIONS(description="A cél BigQuery dataset neve, ahová a RAW tábla kerül."),
  target_table STRING NOT NULL OPTIONS(description="A cél BigQuery RAW tábla neve."),
  write_disposition STRING NOT NULL OPTIONS(description="A BigQuery betöltés módja, például WRITE_APPEND vagy WRITE_TRUNCATE."),
  autodetect BOOL NOT NULL OPTIONS(description="Azt jelzi, hogy a BigQuery próbáljon-e automatikus sémadetektálást használni."),
  header_row INT64 NOT NULL OPTIONS(description="A forrásfájl azon sora, amely az oszlopneveket tartalmazza."),
  skip_rows INT64 NOT NULL OPTIONS(description="A beolvasás elején kihagyandó sorok száma."),
  field_delimiter STRING OPTIONS(description="CSV forrás esetén a mezőelválasztó karakter."),
  encoding STRING OPTIONS(description="CSV forrás esetén a fájl karakterkódolása."),
  expected_columns ARRAY<STRING> OPTIONS(description="Azoknak az oszlopoknak a listája, amelyeknek kötelezően szerepelniük kell a forrásban."),
  target_schema ARRAY<STRUCT<
    column_name STRING OPTIONS(description="A cél BigQuery oszlop neve."),
    data_type STRING OPTIONS(description="A cél BigQuery oszlop adattípusa."),
    mode STRING OPTIONS(description="A cél BigQuery oszlop módja, például NULLABLE vagy REQUIRED.")
  >> OPTIONS(description="A cél RAW tábla létrehozásához használt BigQuery séma."),
  add_metadata_columns BOOL NOT NULL OPTIONS(description="Azt jelzi, hogy az importer adjon-e technikai metadata oszlopokat a betöltött adatokhoz."),
  description STRING OPTIONS(description="Rövid üzleti vagy technikai magyarázat az adott betöltési szabályhoz."),
  created_at TIMESTAMP NOT NULL OPTIONS(description="A config sor létrehozásának időpontja."),
  updated_at TIMESTAMP NOT NULL OPTIONS(description="A config sor utolsó módosításának időpontja.")
);

CREATE TABLE IF NOT EXISTS `ford-training-430008.training_config.file_ingestion_run_log`
(
  run_id STRING NOT NULL OPTIONS(description="Az importer futásának egyedi technikai azonosítója."),
  event_id STRING OPTIONS(description="A Pub/Sub vagy Cloud Storage esemény azonosítója, amely a futást elindította."),
  bucket_name STRING OPTIONS(description="Annak a Cloud Storage bucketnek a neve, ahol a forrásfájl található."),
  object_name STRING OPTIONS(description="A feldolgozott Cloud Storage objektum teljes útvonala a bucketen belül."),
  status STRING NOT NULL OPTIONS(description="A feldolgozás eredményállapota, például SUCCESS, FAILED vagy UNKNOWN_CONFIG."),
  message STRING OPTIONS(description="Rövid szöveges üzenet a futás eredményéről vagy hibájáról."),
  config_ids ARRAY<STRING> OPTIONS(description="Azoknak a config soroknak az azonosítói, amelyek alapján a fájl feldolgozása történt."),
  target_tables ARRAY<STRING> OPTIONS(description="Azoknak a BigQuery cél tábláknak a listája, amelyekbe az importer adatot töltött."),
  started_at TIMESTAMP NOT NULL OPTIONS(description="A feldolgozás kezdetének időpontja."),
  finished_at TIMESTAMP NOT NULL OPTIONS(description="A feldolgozás befejezésének időpontja.")
);
