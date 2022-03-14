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

import os
from os.path import join
from PIL import Image, ImageDraw
from google.cloud import documentai_v1 as documentai
from google.cloud import firestore
from pdf2image import convert_from_path

def process_document(
    project_id: str, location: str, processor_id: str, file_path: str
):
    # Instantiates a Synchronous client
    client_options = {
        "api_endpoint": "{}-documentai.googleapis.com".format(location)}
    client = documentai.DocumentProcessorServiceClient(client_options=client_options)

    # The full resource name of the processor, e.g.:
    # projects/project-id/locations/location/processor/processor-id
    # You must create new processors in the Cloud Console first
    resource_name = client.processor_path(project_id, location, processor_id)

    with open(file_path, "rb") as image:
        image_content = image.read()

    # Read the file into memory
    doc = {"content": image_content, "mime_type": "application/pdf"}

    # Configure the process request
    request = documentai.ProcessRequest(name=resource_name, raw_document=doc)

    # Recognizes text entities in the PDF document
    result = client.process_document(request=request)

    return result.document
    

def get_field(field_name: str, document: dict):
    for page in document.pages:
        for form_field in page.form_fields:
            fieldName = get_text(form_field.field_name, document)
            fieldValue = get_text(form_field.field_value, document)
            if field_name in fieldName:
                return fieldValue
    return None


def get_text(doc_element: dict, document: dict):
    """
    Document AI identifies form fields by their offsets
    in document text. This function converts offsets
    to text snippets.
    """
    response = ""
    # If a text segment spans several lines, it will
    # be stored in different text segments.
    for segment in doc_element.text_anchor.text_segments:
        start_index = (
            int(segment.start_index)
            if segment in doc_element.text_anchor.text_segments
            else 0
        )
        end_index = int(segment.end_index)
        response += document.text[start_index:end_index]
    return response



def save_processed_document(document, file, incoming_path, outgoing_path):
    db = firestore.Client()
    collection = os.getenv("COLLECTION", "invoices")
    entity = list(filter(lambda entity: "supplier_name" in entity.type_, document.entities))[0]
    company = entity.mention_text
    total = float(get_field("Total", document).replace(",", "")[1:-1])
    paid = float(get_field("Amount Paid", document).replace(",", "")[1:-1])
    
    processed_uri = join(outgoing_path, file)
    labeled_uri = join(outgoing_path, f'labeled-{file}')
    os.rename(incoming_path, processed_uri)
    bounding_box(document, processed_uri, labeled_uri)

    data = {
        "company": company,
        "date": get_field("Date", document).strip(),
        "due_date": get_field("Due Date", document).strip(),
        "total": total,
        "amount_due": total - paid,
        "uri": processed_uri,
        "labeled_uri": labeled_uri,
        "state": "Not Approved"
    }
    db.collection(collection).document(company).set(data)



def bounding_box(document, file_path, labeled_path):
    images = convert_from_path(file_path)
    images[0].save(labeled_path, 'JPEG')
    with Image.open(labeled_path) as labeled:
        draw = ImageDraw.Draw(labeled)
        for entity in document.entities:
            # Draw the bounding box around the entities
            vertices = []
            for vertex in entity.page_anchor.page_refs[0].bounding_poly.normalized_vertices:
                vertices.append({'x': vertex.x * labeled.size[0], 'y': vertex.y * labeled.size[1]})
            draw.polygon([
                vertices[0]['x'], vertices[0]['y'],
                vertices[1]['x'], vertices[1]['y'],
                vertices[2]['x'], vertices[2]['y'],
                vertices[3]['x'], vertices[3]['y']], outline='blue')

        labeled.save(labeled_path)
