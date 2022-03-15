# /usr/env/python3
# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

INCOMING_PREFIX = "incoming/"
PROCESSED_PREFIX = "processed/"

import os
import re
import process
from helpers import get_project_id

from google.cloud import storage


if __name__ == "__main__":
    # Retrieve Jobs-defined env vars
    TASK_NUM = os.getenv("TASK_NUM", 0)
    ATTEMPT_NUM = os.getenv("ATTEMPT_NUM", 0)

    # Retrieve user-defined env vars
    location =  "us"
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", get_project_id())
    processor_id = os.environ["PROCESSOR_ID"]
    bucket_name = os.environ["BUCKET"]

    client = storage.Client()

    for blob in client.list_blobs(bucket_name, prefix=INCOMING_PREFIX):
        if not blob.name.endswith("/"): # Skip folder pseudo-blobs
            print(f"Processing {blob.name}")
            document = process.process_blob(
                project_id, location, processor_id, blob)

            print(f"Done with process_blob for {blob.name}")
            # Save to Firestore

            print(f"Saving info from {blob.name} to Firestore")
            process.save_processed_document(document, blob)

            new_name = f"{PROCESSED_PREFIX}{blob.name[len(INCOMING_PREFIX):]}"
            print(f"Renaming {blob.name} to {new_name}")
            blob.bucket.rename_blob(blob, new_name)
            print("Ready for the next blob")
