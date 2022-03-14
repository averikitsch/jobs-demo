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

import json
import os
import re
from os.path import isdir, isfile, join
import process
from helpers import get_project_id
import sys


if __name__ == "__main__":
    try:
        # Retrieve Jobs-defined env vars
        TASK_NUM = os.getenv("TASK_NUM", 0)
        ATTEMPT_NUM = os.getenv("ATTEMPT_NUM", 0)

        # Retrieve user-defined env vars
        location =  "us" #get_service_region()[0:2] or
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", get_project_id())
        processor_id = os.environ["PROCESSOR_ID"]
        mnt_dir = os.getenv("MNT_DIR", "/mnt/gcs")

        # Throw error if mount path is not a directory
        if not isdir(mnt_dir):
            raise Exception(
                "Mount path is not a directory. Check your MNT_DIR env var.")
        # List files in mount
        incoming_path = join(mnt_dir, "incoming/")
        outgoing_path = join(mnt_dir, "processed/")
        print(os.listdir(mnt_dir))
        print(os.listdir(incoming_path))
        for file in os.listdir(incoming_path):
            full_path = join(incoming_path, file)
            if isfile(full_path):
                print(f"Processing {file}")
                document = process.process_document(
                    project_id, location, processor_id, full_path)

                print(f"Done with {file}")
                # Save to Firestore

                # blob_name references the document in GCS
                blob_name = re.sub(r"^.*/", "", full_path)

                process.save_processed_document(document, blob_id)
                os.rename(full_path, join(outgoing_path, file))

    except Exception as err:
        message = f"Task #{TASK_NUM}, Attempt #{ATTEMPT_NUM} failed: {str(err)}"
        print(json.dumps({"message": message, "severity": "ERROR"}))
        sys.exit(1)  # Retry Job Task by exiting the process
        
