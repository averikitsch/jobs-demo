#/usr/env/python3
 
"""
    Cloud Run Job to OCR text from every PDF with the prefix "incoming/" in
    a bucket, saving the extracted text in the same bucket with the
    "text/" prefix.
 
    Assumptions this makes:
 
    - The source PDFs are all named incoming/<SOMETHING>.pdf
    - The extracted text files will be named text/<SOMETHING>.txt
    - The source PDFs are renamed to processed/<SOMETHING>.pdf to avoid
        being extracted again
    - Files created during the extraction process are in a folder
        named work. They aren't deleted by this program, but it
        is okay to delete that folder after extraction is complete.
"""
 
import json
import re
from google.cloud import storage
from google.cloud import vision
 
 
def text_from_pdf(bucket_name, name):
 
    extract_pages(bucket_name, name)
    merge_text(bucket_name, name)
    move_source_pdf(bucket_name, name)
 
    text_uri = f"{bucket_name}/text/{name}.txt"
    return text_uri
 
 
def extract_pages(bucket_name, name):
 
    source_uri = f"gs://{bucket_name}/incoming/{name}.pdf"
    dest_uri = f"gs://{bucket_name}/work/{name}/"
 
    print(f"Starting to extract text from {source_uri}")
 
    mime_type = 'application/pdf'
    batch_size = 5  # Most pages per operation supported
 
    client = vision.ImageAnnotatorClient()
 
    feature = vision.Feature(
        type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)
 
    gcs_source = vision.GcsSource(uri=source_uri)
    input_config = vision.InputConfig(
        gcs_source=gcs_source, mime_type=mime_type)
 
    gcs_destination = vision.GcsDestination(uri=dest_uri)
    output_config = vision.OutputConfig(
        gcs_destination=gcs_destination, batch_size=batch_size)
 
    async_request = vision.AsyncAnnotateFileRequest(
        features=[feature], input_config=input_config,
        output_config=output_config)
 
    operation = client.async_batch_annotate_files(
        requests=[async_request])
 
    operation.result(timeout=420)   # Plenty of time even for large books
    print(f"Finished extracting json data from {source_uri} to {dest_uri}")
 
    return
 
 
def merge_text(bucket_name, name):
    print(f"Merging text from {bucket_name}/work/{name}/")    
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
 
    full_text = ''
 
    blob_list = [blob for blob in list(bucket.list_blobs(
        prefix=f"work/{name}/")) if not blob.name.endswith('/')]
    print(f"Found {len(blob_list)} JSON files to process")
 
    for blob in sorted(blob_list, key=first_page_number):
        print(f"Processing blob named {blob.name}")        
        json_string = blob.download_as_string()
        response = json.loads(json_string)
        for r in response['responses']:
            print(f"Processing json data from {blob.name}")            
            if 'fullTextAnnotation' in r and 'text' in r['fullTextAnnotation']:
                text = r['fullTextAnnotation']['text']
                print(f"Found {len(text)} bytes of text.")
                full_text += "\n" + text
            else:
                print(f"Blob doesn't have text: {r}")
 
    blob_name = f"text/{name}.txt"
    print(f"Uploading {len(full_text)} bytes to blob named {blob_name}")
    bucket.blob(blob_name).upload_from_string(full_text)
    print("Uploaded.")
    return full_text
 
 
def first_page_number(blob):
    name = blob.name
    matches = re.search(r'-(\d+)-', name)
    page_number = int(matches.group(1))
    return page_number
 
 
def move_source_pdf(bucket_name, name):
    # Source blob name is incoming/{name}.pdf.
    # Move (rename) it to processed/{name}.pdf
 
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f"incoming/{name}.pdf")
    print(f"Blob is named {blob.name}")
 
    bucket.rename_blob(blob, f"processed/{name}.pdf")
 
 
if __name__ == "__main__":
    client = storage.Client()
    for pdf in client.list_blobs("engelke-crj-friction", prefix="incoming/"):
        print(f"About to process {pdf.name}")
 
        filename = pdf.name[9:]
        if not filename.endswith(".pdf"):
            print(f"Source file doesn't end with .pdf: {filename}")
            continue
 
        name = filename[:-4]
        print(f"Extracting text from {filename}")
        text_from_pdf("engelke-crj-friction", name)
        print(f"Done with {filename}")