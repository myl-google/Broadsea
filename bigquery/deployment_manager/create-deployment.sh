gcloud deployment-manager deployments create ohdsi-deployment --config ohdsi.yaml &&
gcloud compute instances stop ohdsi-deployment-vm --zone us-central1-a &&
gcloud sql users create ohdsi-postgres-user % --instance=ohdsi-deployment-postgres-c --password=ohdsi-postgres-password &&
gcloud compute instances start ohdsi-deployment-vm --zone us-central1-a
