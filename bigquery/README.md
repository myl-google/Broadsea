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
sudo apt-get update
sudo apt-get install git
git clone https://github.com/myl-google/Broadsea.git
cd Broadsea/bigquery
```

### Deployment manager

gcloud compute instances describe broadsea-deployment-broadsea-vm
gcloud deployment-manager deployments describe broadsea-deployment
gcloud deployment-manager deployments create broadsea-deployment --config broadsea_deployment.yaml
gcloud deployment-manager deployments delete broadsea-deployment 

permission postgres to the vm ip address - verify that you can connect with the default password without having to set it
switch to cos or kubernetes and run both broadsea containers in one vm 
(gke may be tricky to use a non-ephemeral address, cos requires using cloud init)

cos requires using cloud init
cos requires finding the right image

dump the table schemas and convert them to deployment manager
create the tables in the datasets (will need to keep the schema up to date)

see if starschema can already fetch from default credentials with the right arguments (seems like it can be done with minor code changes)
confirm credentials are in the vm
confirm credentials are in the container
figure out if bigquery can authorize from the vm and from the container (make code changes to starschema if necessary)
try to add a secret to the broadsea_manifest (or figure out how to authorize in the container)

populate source table in postgres on startup
set the correct postgres ip in the environment variable in the vm
get the bigquery driver into the container - may need to build your own image to make this work; could also check it into the webapi install; could also check it alongside the main broadsea dockerfile
build the broadsea images and host them on gcr (faster and you can also test them)

### Alternative 

- create two external ip addresses in cloud shell
```bash
export PROJECT_ID=`gcloud config get-value project`
gcloud config set project ${PROJECT_ID?}
export PROJECT_NUMBER=`gcloud projects list --format 'value(PROJECT_NUMBER)' --filter PROJECT_ID=$PROJECT`
export REGION=us-central1
export ZONE=us-central1-a
gcloud config set compute/zone ${ZONE?}

# Create service account key
gcloud iam service-accounts keys create ohdsi-bigquery.p12 --iam-account ${PROJECT_NUMBER?}-compute@developer.gserviceaccount.com --key-file-type=p12
gsutil mb -c regional -l ${REGION?} gs://bigquery-key-${PROJECT_NUMBER?}
gsutil cp ohdsi-bigquery.p12 gs://bigquery-key-${PROJECT_NUMBER?}/
rm ohdsi-bigquery.p12

# Create cloud sql postgres instance
TODO

# Create gke cluster 
gcloud components install kubectl
gcloud container clusters create broadsea-cluster --num-nodes=1
# Can't be used in combination with --num-nodes=1 --machine-type=f1-micro
gcloud alpha container clusters create broadsea-cluster --enable-kubernetes-alpha # until 1.8 is available

# Deploy both containers
kubectl create secret generic ohdsi-bigquery --from-file=./ohdsi-bigquery.p12 # https://kubernetes.io/docs/concepts/configuration/secret/
# TODO - create a yaml file
# (cancelled) build a local image with the p12 file included and upload to gcr (need to enable gcr with glcoud service-management enable ... ...)
# (cancelled) create a gcePersistentDisk 
# (cancelled) copy the p12 file using a gcs command run as part of starting the container (need to ensure gsutil is installed, also need to authenticate from inside the container) - could use a kubectl cp before running anything and on any restart
# TODO - set environment variables with jdbc urls, passwords, etc. using --env="var=value" on the run command or in the yaml file
kubectl run broadsea-methods --image=ohdsi/broadsea-methodslibrary --port=8787
kubectl create -f broadsea
# Use a multi-container pod https://lukemarsden.github.io/docs/user-guide/pods/multi-container/

# Port forwarding
gcloud --project ${PROJECT_ID?} --zone=${ZONE?} container clusters get-credentials broadsea-cluster
export METHODS_PODNAME=`kubectl get pods -o jsonpath={.items..metadata.name} --selector=run=broadsea-methods`
kubectl port-forward ${METHODS_PODNAME?} 8787:8787

# Shell to containers
kubectl exec broadsea-methods-1737533209-ngb7l -i -t -- bash
kubectl exec broadsea-webtools-3776678029-hpnwj -t -i -- more /var/log/supervisor/deploy-script-stderr---supervisor-jii9ye.log


# Old
gcloud compute addresses create broadsea-methods-ip --region ${REGION?}
export BROADSEA_METHODS_IP=`gcloud compute addresses describe broadsea-methods-ip --region ${REGION?} --format 'value(address)'`
gcloud compute addresses create broadsea-webtools-ip --region ${REGION?}
export BROADSEA_WEBTOOLS_IP=`gcloud compute addresses describe broadsea-webtools-ip --region ${REGION?} --format 'value(address)'`
gcloud compute --project "${PROJECT?}" instances create "broadsea-methods-vm" \
--zone "${REGION?}-a" \
--machine-type "n1-standard-1" \
--subnet "default" \
--address ${BROADSEA_METHODS_IP?} \
--metadata "gce-container-declaration=spec:\u000a  containers:\u000a    - name: broadsea-methods-vm\u000a      image: ohdsi/broadsea-methodslibrary\u000a      volumeMounts:\u000a        - name: host-path-1\u000a          mountPath: /tmp/drivers\u000a          readOnly: true\u000a      stdin: false\u000a      tty: false\u000a  restartPolicy: Always\u000a  volumes:\u000a    - name: host-path-1\u000a      hostPath:\u000a        path: /tmp/drivers\u000a" \
--maintenance-policy "MIGRATE" \
--service-account "${PROJECT_NUMBER?}-compute@developer.gserviceaccount.com" \
--scopes "https://www.googleapis.com/auth/cloud-platform" \
--image "cos-beta-62-9901-37-0" \
--image-project "cos-cloud" \
--boot-disk-size "10" \
--boot-disk-type "pd-standard" \
--boot-disk-device-name "broadsea-methods-vm"


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
