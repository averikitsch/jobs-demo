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

from flask import Flask, redirect, render_template, request
import os

from google.cloud import firestore
from google.cloud import storage


app = Flask(__name__)


@app.route("/", methods=["GET"])
def show_list_to_review():
    db = firestore.Client()
    colref = db.collection("invoices")
    query = colref.where("state", "==", "Not Processed")
    invoices = [rec.to_dict() for rec in query.stream()]
    return render_template("list.html", invoices=invoices), 200


@app.route("/<invoice_id>", methods=["GET"])
def show_invoice_to_review(invoice_id):
    BUCKET_NAME = os.environ.get("BUCKET")
    client = storage.Client()

    try:
        bucket = client.get_bucket(BUCKET_NAME)
    except Exception as e:
        return f"Could not open bucket: {e}", 400

    return render_template("invoice.html"), 200


@app.route("/<invoice_id>", methods=["POST"])
def update_status(invoice_id):
    db = firestore.Client()

    return redirect("/")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)