import process
import os
import datetime
from os.path import isdir, isfile, join

def write_file(mnt_dir, filename, content):
    '''Write files to a directory with date created'''
    date = datetime.datetime.utcnow()
    file_date = '{dt:%a}-{dt:%b}-{dt:%d}-{dt:%H}:{dt:%M}-{dt:%Y}'.format(dt=date)
    with open(f'{mnt_dir}/{filename}-{file_date}.html', 'a') as f:
        f.write(content)

if __name__ == "__main__":
    location = "us" # compute get region?
    project_id = os.environ["GOOGLE_CLOUD_PROJECT"]
    processor_id = os.environ["PROCESSOR_ID"]
    path = os.environ.get('MNT_DIR', '/mnt/gcs')

    
    if not isdir(path):
        Exception("oops")

    for file in os.listdir(path):
        full_path = join(path, file)
        if isfile(full_path):
            document = process.process_document(project_id, location, processor_id, full_path)
            print(f"Done with {file}")
            process.save_processed_document(document)

    html = process.summarize()
    write_file(path + "/summaries", "summary", html)