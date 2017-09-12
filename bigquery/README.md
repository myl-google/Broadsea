# Additional Notes for Running with BigQuery

## Creating the CDM schema

- Install the cloud SDK: https://cloud.google.com/sdk/docs/
- wget https://raw.githubusercontent.com/OHDSI/CommonDataModel/master/PostgreSQL/OMOP%20CDM%20ddl%20-%20PostgreSQL.sql
- Create a target dataset, e.g. "cdm", in your cloud project https://bigquery.cloud.google.com
- python create_cdm_tables.py -p project_name -d dataset_name

## Using PostgreSQL for OHDSI tables

The OHDSI tables are stored in PostgreSQL, not BigQuery, since the latter doesn't support JPA, Flyway etc.

TODO(myl): instructions to create a suitable PostgreSQL database using cloud sql.
