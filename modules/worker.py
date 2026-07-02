import threading
import requests as r
import shutil
import time
import os

WORKING = False # global working indicator variable
api = 'https://appeears.earthdatacloud.nasa.gov/api/' # AppEEARS api url

def retrieve_data(queue):
    ''' internal process of server. check status of point request and retreive data from AppEEARS and generate predictions. 
    code from https://github.com/nasa/AppEEARS-Data-Resources/blob/main/Python/tutorials/AppEEARS_API_Point.ipynb '''
    global WORKING
    WORKING = True

    destDir = 'modules/appeears_data'
    files = {}

    while not queue.isEmpty():
        payload = queue.dequeue() # retreive request in front and dequeue
        head = {'Authorization': 'Bearer {}'.format(payload.token)}  # Create a header to store token information,

        # check status of point request with 1 minute interval
        starttime = time.time()
        while r.get('{}task/{}'.format(api, payload.taskId), headers=head).json()['status'] != 'done':
            print(f'point request completion status for {payload.email} | {r.get('{}task/{}'.format(api, payload.taskId), headers=head).json()['status']}')
            time.sleep(60.0 - ((time.time() - starttime) % 60.0))

        # retrieve file from AppEEARS
        if not os.path.exists(destDir): os.mkdir(destDir) # create directory
        bundle = r.get('{}bundle/{}'.format(api,payload.taskId), headers=head).json()  # Call API and return bundle contents for the task_id as json

        for f in bundle['files']: 
            files[f['file_id']] = f['file_name'] # Fill dictionary with file_id as keys and file_name as values

        for f in files:
            dl = r.get('{}bundle/{}/{}'.format(api, payload.taskId, f), headers=head, stream=True, allow_redirects = "TRUE")  # Get a stream to the bundle file
            if files[f].endswith('.tif'):
                filename = files[f].split('/')[1]
            else:
                filename = files[f]
            filepath = os.path.join(destDir, filename) # Create output file path
            with open(filepath, 'wb') as f: # Write file to dest dir
                for data in dl.iter_content(chunk_size=8192): f.write(data) 

        if os.path.exists(destDir): shutil.rmtree(destDir) # remove directory after process 
    
    WORKING = False
    return

def start_worker(queue):
    ''' return if worker is already working '''
    global WORKING

    if WORKING: return 
    if queue.isEmpty(): return
    
    # execute each request in queue as threads running one at a time
    threading.Thread(target=retrieve_data, args=(queue,), daemon=True).start()
    return 
