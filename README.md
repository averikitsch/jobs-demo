# Cloud Run Jobs - Invoice Processor

* Invoices are manually uploading to GCS 
* A Cloud Run Job processes all invoices and produces a report
* Cloud Scheduler runs the job every night

Currently the Document AI integration with GCS is not working. Therefore this sample uses the 2nd Gen environment to mount a GCS bucket similar to [Using Cloud Storage FUSE with Cloud Run tutorial](https://cloud.google.com/run/docs/tutorials/network-filesystems-fuse).

# Deploying
* Enable Document AI, Cloud Run, Firestore, Scheduler APIs for your project

* Create a Firestore database

* [Create a Document AI processor in the console](https://cloud.google.com/document-ai/docs/create-processor#create-processor):
    * Select Invoice Parser. Learn more about the [Invoice Parser](https://cloud.google.com/document-ai/docs/processors-list#processor_invoice-processor)
    * Give your processor a name, `my-invoice-processor`
    * Save the resulting Processor ID or retrieve 

    ```
    export PROCESSOR_ID=<>
    export GOOGLE_CLOUD_PROJECT=<>
    ```

  We will be using the small file online processing request type for a synchronous response

* Make a GCS bucket
  ```
  gsutil mb -l us-central1 gs://$GOOGLE_CLOUD_PROJECT-invoices
  ```

* Add some invoices
  ```
  gsutil cp -r incoming/*.pdf gs://$GOOGLE_CLOUD_PROJECT-invoices/incoming
  ```

* Build the container
  ```
  gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/invoice-processor
  ```

* Create the job
  ```
  gcloud alpha run jobs create invoice-processing \
      --image gcr.io/$GOOGLE_CLOUD_PROJECT/invoice-processor \
      --execution-environment gen2 \
      --region us-central1 \
      --set-env-vars BUCKET=$GOOGLE_CLOUD_PROJECT-invoices \
      --set-env-vars PROCESSOR_ID=$PROCESSOR_ID \
      --set-env-vars GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT
  ```

* Run the job

  ```
  gcloud alpha run jobs run invoice-processing --region us-central1
  ```

  or update Cloud Build's permissions to deploy to Cloud Run and run:

  ```
  gcloud builds submit --config deploy.cloudbuild.yaml
  ```

# Local testing

Use `export MNT_DIR=$(pwd)`

# Scheduler
```
gcloud iam service-accounts create process-identity

# TODO: confirm working
gcloud alpha run jobs add-iam-policy-binding invoice-processing \
  --member serviceAccount:process-identity@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com \
  --role roles/run.invoker
```
Every day at midnight:
```
gcloud scheduler jobs create http my-job \
  --schedule="0 0 * * *" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$GOOGLE_CLOUD_PROJECT/jobs/invoice-processing:run" \
  --http-method=POST \
  --oauth-service-account-email=process-identity@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com
```