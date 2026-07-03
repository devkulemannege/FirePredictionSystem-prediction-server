import threading
import requests as r
import traceback
import shutil
import time
import os

from . import prediction_worker, error_mail

WORKING = False # global working indicator variable
api = 'https://appeears.earthdatacloud.nasa.gov/api/' # AppEEARS api url

def retrieve_data(queue, app):
    ''' internal process of server. check status of point request and retreive data from AppEEARS and generate predictions. 
    code from https://github.com/nasa/AppEEARS-Data-Resources/blob/main/Python/tutorials/AppEEARS_API_Point.ipynb '''
    global WORKING
    WORKING = True

    destDir = 'modules/appeears_data'
    files = {}

    with app.app_context(): # add thread to flask context
        while not queue.isEmpty():
            payload = queue.dequeue() # retreive request in front and dequeue
            head = {'Authorization': 'Bearer {}'.format(payload.token)}  # Create a header to store token information,

            try:
                # check status of point request with 1 minute interval
                starttime = time.time()
                while r.get('{}task/{}'.format(api, payload.taskId), headers=head).json()['status'] != 'done':
                    print(f'AppEEARS request status -> {payload.email} | {r.get('{}task/{}'.format(api, payload.taskId), headers=head).json()['status']}')
                    time.sleep(300.0 - ((time.time() - starttime) % 300.0))

                # retrieve file from AppEEARS
                if os.path.exists(destDir): 
                    shutil.rmtree(destDir) 
                    os.mkdir(destDir) # remove direcotry if exists and then create empty dir
                else:
                    os.mkdir(destDir)
            except Exception as e:
                print(f'\n--Failed to prepare data directory for {payload.email} | {e}--')
                traceback.print_exc() # print traceback for debugging
                error_mail.send(payload.email) # error mail incase main process fails

                WORKING = False
                return

            try:
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
            except Exception as e:
                print(f'\n--Failed to retreive data from AppEEARS for {payload.email} | {e}--')
                traceback.print_exc() # print traceback for debugging
                error_mail.send(payload.email) # error mail incase main process fails

                WORKING = False
                return 

            # start prediction and mail process
            prediction_worker.start(payload.email) 
            print(f'process finished for {payload.email}')

            if os.path.exists(destDir): shutil.rmtree(destDir) # remove directory after process 
    
    WORKING = False
    return

def start_worker(queue, app):
    ''' return if worker is already working '''
    global WORKING

    if WORKING: return 
    if queue.isEmpty(): return
    
    # execute each request in queue as threads running one at a time
    try:
        threading.Thread(
            target=retrieve_data, 
            args=(queue, app,), 
            daemon=True
        ).start()
    except Exception as e:
        print(f'\n--Failed to start worker thread for {queue.dequeue().email} | {e}--')
        traceback.print_exc() # print traceback for debugging
        error_mail.send(queue.dequeue().email) # error mail incase main process fails

        WORKING = False
    return 
