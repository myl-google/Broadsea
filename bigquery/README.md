# Additional Notes for Running with BigQuery

## Creating a VM to run BroadSea

- Go to https://console.cloud.google.com/compute and click "create instance"
- Under "identity and access" click "set access for each API" and then set
  "Cloud SQL" and "BigQuery" to "enabled"
- Adjust any other settings as desired or leave the defaults.  The VM will fall
  into the free tier if you change the machine type to "micro"
- Click "create"
- In the list of instances, click "SSH" to open a console
- Execute the following in the console

```bash
sudo apt-get install git
git clone https://github.com/myl-google/Broadsea.git
cd BroadSea/bigquery
```

## Creating the CDM schema in BigQuery

- Create a target bigquery dataset, e.g. "cdm", in your cloud project at
  https://bigquery.cloud.google.com
- Execute the following where <dataset_name> is the name of the dataset you just
  created and <project_name> is hte name of your project

``` bash
wget https://raw.githubusercontent.com/OHDSI/CommonDataModel/master/PostgreSQL/OMOP%20CDM%20ddl%20-%20PostgreSQL.sql
python create_cdm_tables.py -p <project_name> -d <dataset_name>
```

## Creating Cloud SQL instance for OHDSI tables

The OHDSI tables are stored in PostgreSQL, not BigQuery, since the latter
doesn't support JPA, Flyway etc.  To create a PostgreSQL instance in Cloud SQL:

- Go to https://console.cloud.google.com/sql and click "create instance"
- Select "postgres"
- Enter an instance name and default password
- Choose a region and zone or leave the defaults
- Adjust any other settings as desired or leave the defaults
- Click "create"
- Make a note of the default password and the IP address of the instance. You'll
  need these when following the BroadSea deployment instructions below

## Create a p12 file for BroadSea to authorize to bigquery

- Go to https://console.cloud.google.com/apis/credentials and click "create
  credentials" then select "service account key"
- Select "Compute Engine default service account" and "P12"
- Click "create"
- Transfer the .p12 file from your local computer to the VM by going to
  https://console.cloud.google.com/storage creating a bucket and then uploading
  the file. Next, in the VM console, run the following command substituting the
  bucket name you just created and the name of the p12 file you uploaded:
``` bash
gsutil cp gs://<bucket_name>/<p12_file_name> ohdsi-bigquery.p12
```

## Run the BroadSea deployment instructions

- Go to https://github.com/OHDSI/Broadsea and search for "Quick Start Broadsea
  Deployment Instructions"
- Follow the instructions with the following modifications:
  - Unless you changed the OS default when creating the VM, you should follow
    the docker installation instructions for Docker CE on Debian.  Make sure to
  - Use the docker-compose.yml file in ~/Broadsea/bigquery.  Change
    datasource.password to the default password you entered when creating your
    cloud sql instance.  Change the IP address in the datasource.url and the
    flyway.datasource.url to the IP that you noted when creating your cloud sql
    instance
  - Use the source_source_daimon.sql file in ~/Broadsea/bigquery.  Change the
    "project_name" in the source_connection string to the name of your project
    and the "user" argument to the default compute engine service.  The service
    account can be found at
    https://console.cloud.google.com/iam-admin/iam/project with the name "Compute Engine default service account" and will be of the
    form 1234567-compute@developer.gserviceaccount.com
