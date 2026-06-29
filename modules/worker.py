from modules.request_queue import request_queue

global WORKING 
WORKING = False

def start_worker():
    if not WORKING:
        if request_queue.getFront():
            WORKING = True
            request = request_queue.dequeue()
            # TODO: complete worker logic
        else:
            WORKING = False
    else:
        return 'internal worker already running.'
