gcloud compute ssh broadsea-deployment41-vm --project ohdsi-in-a-box --zone us-central1-a --ssh-flag="-L" --ssh-flag="8080:localhost:8080" --ssh-flag="-L" --ssh-flag="8787:localhost:8787"
