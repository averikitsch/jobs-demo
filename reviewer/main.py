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

"""
    Web app to review information extracted from submitted invoices, and
    mark the result from the review.

    A separate app enables vendors to submit invoices, and the main Cloud Run
    Jobs app extracts the data.

    Requirements:

    -   Python 3.7 or later
    -   All packages in requirements.txt installed
    -   A bucket with the invoice files in the /processed folder
    -   Firestore database with information about those invoices
    -   Software environment has ADC or other credentials to read from the
        bucket (in order to display to the reviewer), and to read and write
        to the Firestore database (to display information and update status)
    -   The name of the bucket (not the URI) in the environment variable BUCKET

    This Flask app can be run directly via "python main.py" or with gunicorn
    or other common WSGI web servers.
"""

from datetime import timedelta
import os

from flask import Flask, redirect, render_template, request

from google import auth
from google.cloud import firestore
from google.cloud import storage

from google.auth.transport import requests


BUCKET_NAME  = os.environ.get("BUCKET")
PROCESSED_PREFIX = "processed/"
APPROVED_PREFIX = "approved/"

app = Flask(__name__)


@app.route("/", methods=["GET"])
def show_list_to_review():
    db = firestore.Client()
    colref = db.collection("invoices")
    query = colref.where("state", "==", "Not Approved")

    invoices = [rec.to_dict() for rec in query.stream()]

    gcs = storage.Client()
    print(f"GCS client is {gcs}")
    bucket = gcs.get_bucket(BUCKET_NAME)
    print(f"Bucket name {BUCKET_NAME} and bucket is {bucket}")

    credentials, project_id = auth.default()
    if credentials.token is None:
        credentials.refresh(requests.Request())
    for invoice in invoices:
        full_name = f"{PROCESSED_PREFIX}{invoice['blob_name']}"
        print(f"Blob full name is {full_name}")
        blob = bucket.get_blob(full_name)
        url = "None"
        if blob is not None:
            url = blob.generate_signed_url(
                version="v4", expiration=timedelta(hours=1), 
                service_account_email=credentials.service_account_email,
                access_token=credentials.token, method="get", scheme="https")
            print(f"url is {url}")
        invoice["url"] = url

    print(invoices)

    return render_template("list.html", invoices=invoices), 200


@app.route("/", methods=["POST"])
def approve_selected_invoices():
    db = firestore.Client()

    print("Processing the POST form")
    print(request.form)

    for blob_name in request.form.keys():
        print(f"Form item: {blob_name}")
        docref = db.collection("invoices").document(blob_name)
        info = docref.get().to_dict()
        info["state"] = "Approved"
        docref.set(info)
        
    print("Finished processing the POST form")
    return redirect("/")


@app.route("/<invoice_id>", methods=["POST"])
def update_status(invoice_id):
    db = firestore.Client()

    return redirect("/")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)