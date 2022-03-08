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

import google.auth
import requests
import datetime
from google.cloud import storage

METADATA_URI = "http://metadata.google.internal/computeMetadata/v1/"


def get_project_id() -> str:
    """Use the 'google-auth-library' to make a request to the metadata server or
    default to Application Default Credentials in your local environment."""
    _, project = google.auth.default()
    return project


def get_service_region() -> str:
    """Get region from local metadata server
    Region in format: projects/PROJECT_NUMBER/regions/REGION"""
    slug = "instance/region"
    data = requests.get(METADATA_URI + slug, headers={"Metadata-Flavor": "Google"})
    return data.content


def write_file(mnt_dir, filename, content):
    """Write files to a directory with date created"""
    date = datetime.datetime.utcnow()
    file_date = '{dt:%a}-{dt:%b}-{dt:%d}-{dt:%H}:{dt:%M}-{dt:%Y}'.format(dt=date)
    with open(f'{mnt_dir}/{filename}-{file_date}.html', 'a') as f:
        f.write(content)


def move_source_pdf(bucket_name, name):
    # Source blob name is incoming/{name}.pdf.
    # Move (rename) it to processed/{name}.pdf
 
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f"incoming/{name}.pdf")
    print(f"Blob is named {blob.name}")
 
    bucket.rename_blob(blob, f"processed/{name}.pdf")
 