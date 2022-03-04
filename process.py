# /usr/env/python3
from google.cloud import documentai_v1 as documentai


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


def summarize():
    html = '<html><body><table><tr><th>Invoicee</th><th>Balance Due</th></tr>'
    for bill in example_db:
        html += f'<tr><td>{bill["name"]}</td><td>{bill["total"]}</td></tr>'

    html += '</table></body></html>\n'
    return html


example_db = []

def save_processed_document(document):
    example_db.append({"name": get_field("Bill", document), "total": get_field("Balance Due", document)})
    # print(example_db)
    

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