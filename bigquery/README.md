# Deployment manager instructions for Broadsea on Bigquery

Use the provided deployment manager configs method.  An alternative, more
manual, approach is also detailed in the "manual setup instructions for
Broadsea using docker-compose in a VM" section below.

To create a deployment, either use an existing GCP project or create one as a
free trial at https://cloud.google.com/ .  Next, working from the machine where
you want to view the OHDSI tools in the browser, install the Cloud SDK by
following the instructions at https://cloud.google.com/sdk/downloads and run
the following two commands to login and set your default project id.

```
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

Next, download the configs and scripts at
https://github.com/myl-google/Broadsea/tree/master/bigquery/deployment_manager
.  You can either download the individual files or use the link at
https://github.com/myl-google/Broadsea/archive/master.zip to get the whole
repository, then unzip it and change to the bigquery/deployment_manager
subdirectory.

Edit ohdsi.yaml and update the zone or dataset names if desired.  Documentation
is available in ohdsi.jinja.schema.

Now you can run the following to create a full deployment:

```
create-deployment.sh
```

This will take several minutes and create a VM to run Broadsea (which
includes RStudio and Atlas), a Postgresql instance to host the OHDSI
database schema, and bigquery datasets and tables to host the Common
Data Model (aka OMOP) schema.  It is recommended that you load your
data into the created Bigquery tables to ensure that the schema
version matches what is expected by the software.  However, it is also
possible to point the deployment at existing data.  Avoid changing the
schema of the tables when you load them since the OHDSI software
expects the specific schema version that was used to create the
tables.  For example, if you're loading CSVs into the person table
from the proj1 project then first run "bq --project_id proj1 show
--schema cdm1.person" to get the json schema and then use that schema
to load the csv.  Alternatively, you can load the CSV into a temporary
staging table and then run a select statement that re-arranges,
renames, and casts columns as needed and writes the result to a
destination table using "append to table" to avoid changing the
schema.

After your data is loaded, you can ssh to the VM:

```
connect.sh
```

When the connection is open, it does port forwarding so that you can access the
web server running on the VM from your local machine. You must have a
connection open every time you wish to access the web tools.

You can now connect to RStudio by visting http://localhost:8787 in your
browser.  The default username and password are both "rstudio".  To run the
achilles analysis scripts, execute the following in Rstudio:

```
source('/ohdsi-scripts/runAchilles.R')
```

To open Atlas, visit http://localhost:8080/atlas in your browser.  There is a
link to the user guide from the default Home page.

## Deployment details

The deployment creates a GCE VM running [container optimized
OS](https://cloud.google.com/container-optimized-os/docs/) and uses
[cloud-init](http://cloudinit.readthedocs.io/en/latest/index.html#) to
populate several configuration scripts in the VM.  Look at the
metadata of the compute.v1.instance in ohdsi.jinja for details.
Explanations of each file:

- /etc/systemd/system/broadsea-methods.service - a systemd service
  that runs a docker container from an image hosted on the [GCP
  container registry](https://cloud.google.com/container-registry/) in
  the cloud-healthcare-containers project. The image is built from a
  fork of the Broadsea-MethodsLibrary project that has been customized
  to run as part of the deployment:
  https://github.com/myl-google/Broadsea-MethodsLibrary

- /etc/systemd/system/broadsea-webtools.service - same as the previous
  item but with an image built from
  https://github.com/myl-google/Broadsea-WebTools

- /etc/ohdsi-scripts/source_source_daimon.sql and
  /etc/ohdsi-scripts/update_source.py and
  /etc/systemd/system/broadsea-update-source.service - these define a
  systemd service that populates the source rows in the postgres
  database with references to the bigquery datasets when the VM is
  first started

- /etc/ohdsi-scripts/runAchilles.R - installs packages needed for
  achilles from local copies and then runs the achilles analyses

- /etc/ohdsi-scripts/tail_weblog.sh - displays logs of webapi
  interaction with bigquery as they happen

In addition to the VM, the deployment includes a [cloud sql
postgres](https://cloud.google.com/sql/docs/postgres/) to host the
OHDSI schema and bigquery datasets to host the CDM schema.

## Debugging

If you can't connect to RStudio or Atlas, then use connect.sh to
connect to the VM and run "docker ps" to confirm the methods and
webtools containers have started (this may take a few minutes after
the VM is first created). If not, some of the following commands are
useful for debugging:

- "sudo systemctl status broadsea-methods.service" or "sudo systemctl
  status broadsea-webtools.service" give details of why the services
  failed

- "sudo journalctl" shows the systemd logs. You can search for
  messages with the substring "broadsea".

- "sudo systemctl start <service name>" and "sudo systemctl stop
  <service name>" can be used to start and stop services from
  /etc/systemd/system as part of investigating

One possible problem is lack of permission to access the images.  If
this happens, then please contact the person that pointed you to these
instructions.

If you encounter problems with functionality in Atlas, run the
tail_weblog.sh script and note any SQL errors that show up while using
the UI.  There are numerous data and schema issues that can happen
when loading data or transforming it to the CDM.  Interpreting the SQL
errors often gives clues about these data problems and how to fix
them.

# Manual setup instructions for Broadsea using docker-compose in a VM

Files relevant to this option are in the docker_compose/ directory.  The deployment manager
option is likely better in almost all cases, but these instructions are retained here for 
historical interest.

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
sudo apt-get update
sudo apt-get install git
git clone https://github.com/myl-google/Broadsea.git
cd Broadsea/bigquery
```

## Creating the CDM schema in BigQuery

- Create three bigquery datasets named "cdm", "ohdsi", and "temp" in your cloud
project at https://bigquery.cloud.google.com.  Give the temp dataset an
expiration of one day
- After the datasets are created, return to the VM and execute the following
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
  external IP of the VM that you noted earlier.
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
  you can view the weblogs in the Broadsea/bigquery/supervisor directory
- To apply the source_source_daimon.sql file after "docker-compose down" use
  the following commmands where <cloud_sql_ip> is the IP of the cloud sql
  instance

```bash
sudo apt-get install postgresql
export CLOUD_SQL_IP=<cloud_sql_ip>
psql "host=$CLOUD_SQL_IP dbname=postgres user=postgres" -f source_source_daimon.sql
```

## Copy a subset of the ohdsi schema from postgres into bigquery

- Confirm that results_tables_whitelist.txt has the same tables as listed at the
  bottom of
  http://www.ohdsi.org/web/wiki/doku.php?id=documentation:software:webapi:multiple_datasets_configuration
- Create the results tables by running the following commands where
  <cloud_sql_ip> is the IP of the cloud sql instance

``` bash
sudo apt-get install postgresql-client
export CLOUD_SQL_IP=<cloud_sql_ip>
export PROJECT=`gcloud config get-value project`
pg_dump "host=$CLOUD_SQL_IP dbname=postgres user=postgres" > ohdsi.sql
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
