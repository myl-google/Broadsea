# Additional Notes for Running with BigQuery

## Creating a VM to run BroadSea

- Go to https://console.cloud.google.com/compute and click "create instance"
- Under "identity and access" click "set access for each API" and then set
  "Cloud SQL" to "enabled"
- Adjust any other settings as desired (or leave the defaults)
- Click "create"
- In the list of instances, click "SSH" to open a console
- Execute the following in the console
```bash
git clone https://github.com/myl-google/Broadsea.git
cd BroadSea
```

## Creating the CDM schema in BigQuery

- Execute the following in the console
```bash
wget https://raw.githubusercontent.com/OHDSI/CommonDataModel/master/PostgreSQL/OMOP%20CDM%20ddl%20-%20PostgreSQL.sql
```

- Create a target bigquery dataset, e.g. "cdm", in your cloud project at
  https://bigquery.cloud.google.com
  
- Execute 
``` bash
python create_cdm_tables.py -p <project_name> -d <dataset_name>
```

## Creating Cloud SQL instance for OHDSI tables

The OHDSI tables are stored in PostgreSQL, not BigQuery, since the latter
doesn't support JPA, Flyway etc.  To create a PostgreSQL instance in Cloud SQL:

- Go to https://console.cloud.google.com/sql and click "create instance"
- Select "postgres"
- Enter an instance name and default password
- Choose a region and zone (or leave the defaults)
- Adjust any other settings as desired (or leave the defaults)




