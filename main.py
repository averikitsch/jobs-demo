import datetime
import json
import os
from os.path import isdir, isfile, join
import process
import sys

def write_file(mnt_dir, filename, content):
    '''Write files to a directory with date created'''
    date = datetime.datetime.utcnow()
    file_date = '{dt:%a}-{dt:%b}-{dt:%d}-{dt:%H}:{dt:%M}-{dt:%Y}'.format(dt=date)
    with open(f'{mnt_dir}/{filename}-{file_date}.html', 'a') as f:
        f.write(content)

if __name__ == "__main__":
    try:
        TASK_NUM = os.getenv("TASK_NUM", 0)
        ATTEMPT_NUM = os.getenv("ATTEMPT_NUM", 0)
        location = "us" # compute get region?
        project_id = os.environ["GOOGLE_CLOUD_PROJECT"]
        processor_id = os.environ["PROCESSOR_ID"]
        path = os.environ.get('MNT_DIR', '/mnt/gcs')

        
        if not isdir(path):
            raise Exception("oops")

        for file in os.listdir(path):
            full_path = join(path, file)
            if isfile(full_path):
                print(f"Processing {file}")
                document = process.process_document(project_id, location, processor_id, full_path)
                # print(document)
                print(f"Done with {file}")
                process.save_processed_document(document)

        html = process.summarize()
        write_file(path + "/summaries", "summary", html)
    except Exception as err:
        message = f"Task #{TASK_NUM}, Attempt #{ATTEMPT_NUM} failed: {str(err)}"
        print(json.dumps({"message": message, "severity": "ERROR"}))
        sys.exit(1)  # Retry Job Task by exiting the process