# Cloud Run Jobs - Invoice Processor

* Invoices are manually uploading to GCS 
* A Cloud Run Job processes all invoices and produces a report
* Cloud Scheduler runs the job every night

Currently the Document AI integration with GCS is not working. Therefore this sample uses the 2nd Gen environment to mount a GCS bucket similar to [Using Cloud Storage FUSE with Cloud Run tutorial](https://cloud.google.com/run/docs/tutorials/network-filesystems-fuse).

# Deploying
* Enable Document AI API for your project

* [Create a Document AI processor in the console](https://cloud.google.com/document-ai/docs/create-processor#create-processor):
    * Select Invoice Parser. Learn more about the [Invoice Parser](https://cloud.google.com/document-ai/docs/processors-list#processor_invoice-processor)
    * Give your processor a name, `my-invoice-processor`
    * Save the resulting Processor ID or retrieve 

    ```
    export PROCESSOR_ID="cf1dd3f18973a203"
    export GOOGLE_CLOUD_PROJECT="oddjob-friction"
    ```

  We will be using the small file online processing request type for a synchronous response

* Make a GCS bucket
  ```
  gsutil mb gs://oddjob-invoices -l us-central1
  ```

* Add some invoices

* Build the container
  ```
  gcloud builds submit --tag gcr.io/oddjob-friction/invoice-processor
  ```

* Create the job
  ```
  gcloud alpha run jobs create invoice-processing \
      --image gcr.io/oddjob-friction/invoice-processor \
      --execution-environment gen2 \
      --set-env-vars BUCKET=oddjob-invoices \
      --set-env-vars PROCESSOR_ID=$PROCESSOR_ID \
      --set-env-vars GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT
  ```

* Run the job

  ```
  gcloud alpha run jobs run invoice-processing
  ```

# Local testing

Use `export MNT_DIR=$(pwd)/invoices`