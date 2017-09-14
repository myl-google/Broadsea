# Additional Notes for Running with BigQuery

## Creating a VM to run BroadSea

- Go to https://console.cloud.google.com/compute and click "create instance"
- Under "identity and access" click "set access for each API" and then set
  "Cloud SQL" and "BigQuery" to "enabled"
- Click on the "Management, disks, networking, SSH keys" link to expand it then
  click on the "networking" tab, then click on the default network then click on
  the "ephemeral" external ip, create a named ip address and select that.  Note
  the IP address for later
- Adjust any other settings as desired or leave the defaults
- Click "create"
- In the list of instances, click "SSH" to open a console
- Execute the following in the console
```bash
sudo apt-get install git
git clone https://github.com/myl-google/Broadsea.git
cd BroadSea/bigquery
```

## Creating the CDM schema in BigQuery

- Create two bigquery datasets named "cdm" and "ohdsi" in your cloud project at
  https://bigquery.cloud.google.com
- Execute the following
``` bash
export PROJECT=`gcloud config get-value project`
wget https://raw.githubusercontent.com/OHDSI/CommonDataModel/master/PostgreSQL/OMOP%20CDM%20ddl%20-%20PostgreSQL.sql
python create_bigquery_tables.py -p $PROJECT -d cdm -s "OMOP CDM ddl - PostgreSQL.sql"
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
export BUCKET_NAME=<bucket that you just created>
export P12_FILE=<p12 file that you just uploaded>
gsutil cp gs://$BUCKET_NAME/$P12_FILE ohdsi-bigquery.p12
```

## Run the BroadSea deployment instructions

- Do all of the following under ~/Broadsea/bigquery
- Edit the docker-compose.yml file to change datasource.password and
  flyway.datasource.password to the cloud sql password that you configured
  earlier.  Change the IP address in datasource.url and flyway.datasource.url to
  the IP that you noted for the cloud sql instance
- Edit the source_source_daimon.sql file to change the "project_name" in the
  source_connection string to the name of your project and the "user" argument
  to the default compute engine service account.  The account can be found at
  https://console.cloud.google.com/iam-admin/iam/project with the name "Compute
  Engine default service account" and will be of the form
  1234567-compute@developer.gserviceaccount.com
- Go to https://github.com/OHDSI/Broadsea and search for "Quick Start Broadsea
  Deployment Instructions".  Follow the instructions with the following
  modifications
- Unless you changed the OS default when creating the VM, you should follow the
  Docker installation instructions for Docker CE on Debian
- On linux, you need to install Docker Compose after you install CE.  Follow the
  instructions at https://docs.docker.com/compose/install/
- On linux, after installing Docker Compose follow the "Manage docker as
  non-root user" post-installation steps at
  https://docs.docker.com/engine/installation/linux/linux-postinstall/
- Whenever you run "docker-compose up -d" you can use the following command
  after the containers have fully started to view the weblogs and confirm there
  are no errors

``` bash
./copy-weblogs.sh
```

- To apply the source_source_daimon.sql file after "docker-compose down" use
  the following commmands where <cloud_sql_ip> is the IP of the cloud sql
  instance

```bash
sudo apt-get install postgresql
export CLOUD_SQL_IP=<cloud_sql_ip>
psql "host=<cloud_sql_ip> dbname=postgres user=postgres" -f source_source_daimon.sql
```

## Copy a subset of the ohdsi schema from postgres into bigquery

- Confirm that results_tables_whitelist.txt has the same tables as listed at the
  bottom of
  http://www.ohdsi.org/web/wiki/doku.php?id=documentation:software:webapi:multiple_datasets_configuration
- Create the results tables by running the following commands where
  <cloud_sql_ip> is the IP of the cloud sql instance

``` bash
export CLOUD_SQL_IP=<cloud_sql_ip>
export PROJECT=`gcloud config get-value project`
pg_dump "host=$CLOUD_SQL_IP dbname=postgres user=postgres" > ohdsi.sq
python create_bigquery_tables.py -p $PROJECT -d ohdsi -s ohdsi.sql -w results_tables_whitelist.txt
```

## Open Atlas and RStudio from your local machine

- Install the cloud SDK on your local machine where you want to view Atlas in
  the web browser (i.e. not the VM) https://cloud.google.com/sdk/downloads
- Run the following to create an SSH tunnel with port forwarding from your local
  machine to the VM substituting the appropriate values for VM_NAME and VM_ZONE

``` bash
export VM_NAME=<the instance name of the VM>
export VM_ZONE=<the zone of the VM>
export PROJECT=<project name>
gcloud compute ssh $VM_NAME --project $PROJECT --zone $VM_ZONE --ssh-flag="-L" --ssh-flag="8080:localhost:8080" --ssh-flag="-L" --ssh-flag="8787:localhost:8787"
```

- To open RStudio on your local machine visit http://localhost:8787
- To open Atlas on your local machine visit http://localhost:8080/atlas
