# Additional Notes for Running with BigQuery

## Creating a VM to run BroadSea

- Go to https://console.cloud.google.com/compute and click "create instance"
- Under "identity and access" click "set access for each API" and then set
  "Cloud SQL" and "BigQuery" to "enabled"
- Click on the "Management, disks, networking, SSH keys" link to expand it then
  click on the "networking" tab, then click on the default network then click on
  the "ephemeral" external ip, create a named ip address and select that.  Note
  the IP address for later
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
  created and <project_name> is the name of your project
``` bash
wget https://raw.githubusercontent.com/OHDSI/CommonDataModel/master/PostgreSQL/OMOP%20CDM%20ddl%20-%20PostgreSQL.sql
python create_cdm_tables.py -p <project_name> -d <dataset_name>
```
- At this point, you can either load data into the new schema or continue the
  rest of the setup using the empty database

## Creating Cloud SQL instance for OHDSI tables

The non-CDM OHDSI tables used by the WebAPI are stored in PostgreSQL rather than
BigQuery since the latter doesn't support JPA, Flyway etc.  To create a
PostgreSQL instance in Cloud SQL:

- Go to https://console.cloud.google.com/sql and click "create instance"
- Select "postgres"
- Enter an instance name and default password
- Choose a region and zone or leave the defaults
- Click on "configuration options", select "authorize networks", and add the
  external IP of the VM that you noted earlier
- Adjust any other settings as desired or leave the defaults
- Click "create"
- Go to
  https://console.cloud.google.com/apis/api/sqladmin.googleapis.com/overview and
  click "enable".  (This is necessary to allow the "gcloud sql" command that is
  used later)
-
- Make a note of the name of the instance, the default password, and the IP
  address for later

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
- Follow the instructions with the following modifications
- Unless you changed the OS default when creating the VM, you should follow the
  Docker installation instructions for Docker CE on Debian
- On linux, you need to install Docker Compose after you install CE.  Follow the
  instructions at https://docs.docker.com/compose/install/
- On linux, after installing Docker Compose follow the "Manage docker as
  non-root user" post-installation steps at
  https://docs.docker.com/engine/installation/linux/linux-postinstall/
- Edit the docker-compose.yml file in ~/Broadsea/bigquery to change
  datasource.password and flyway.datasource.password to the default cloud sql
  password.  Change the IP address in datasource.url and flyway.datasource.url
  to the IP that you noted for the cloud sql instance
- Edit the source_source_daimon.sql file in ~/Broadsea/bigquery to change the
  "project_name" in the source_connection string to the name of your project and
  the "user" argument to the default compute engine service account.  The
  account can be found at https://console.cloud.google.com/iam-admin/iam/project
  with the name "Compute Engine default service account" and will be of the form
  1234567-compute@developer.gserviceaccount.com
- To apply the source_source_daimon.sql file after the "docker-compose down" use
  the following commmands where <instance_name> is the name of the cloud sql
  instance

```bash
sudo apt-get install postgresql
gcloud sql connect <instance_name> --user postgres
```
