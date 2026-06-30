class Node:
    ''' Node object which contains each requests' information '''
    def __init__(self, taskId, token, email):
        self.taskId = taskId
        self.token = token
        self.email = email
        self.next = None # next node pointer

class request_queue:
    ''' queue data structure which handles requests '''
    def __init__(self):
        self.front = None
        self.rear = None

    def enqueue(self, taskId, token, email):
        newNode = Node(taskId, token, email) # create Node object

        if self.isEmpty():
            self.front = self.rear = newNode
        else:
            self.rear.next = newNode
            self.rear = newNode

    def dequeue(self):
        if self.front is None:
            return None 
        
        # repalce front with rear and return front 
        tempNode = self.front
        self.front = self.front.next
        if self.front is None:
            self.rear == None

        return tempNode
    
    def getFront(self):
        if self.front is None:
            return None # if front is empty 
        return self.front
    
    def isEmpty(self):
        return self.front is None
