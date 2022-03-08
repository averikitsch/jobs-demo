#/bin/bash

gcloud builds submit --tag gcr.io/oddjob-friction/invoice-processor:5

export BUCKET=oddjob-invoices
export GOOGLE_CLOUD_PROJECT=oddjob-friction
export PROCESSOR_ID=cf1dd3f18973a203

gcloud alpha run jobs update invoice-processing \
    --image gcr.io/oddjob-friction/invoice-processor:5 \
    # --execution-environment gen2 \
    # --update-env-vars BUCKET=$BUCKET \
    # --update-env-vars PROCESSOR_ID=$PROCESSOR_ID \
    # --update-env-vars GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT


gcloud alpha run jobs run invoice-processing


# Create a scheduler job