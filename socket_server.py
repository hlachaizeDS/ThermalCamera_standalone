import os, time

from threading import Thread
import socket
import json

MAX_LENGTH = 4096
is_384=1

class Pipe(Thread):

    def __init__(self):
        Thread.__init__(self,daemon=True)
        self.received=b""
        self.run_name = b""
        self.data = []
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.PORT = 10000
        self.HOST = '127.0.0.1'

        self.serversocket.bind((self.HOST, self.PORT))
        self.serversocket.listen(10)

    def run(self):
        while(1):
            (clientsocket, address) = self.serversocket.accept()

            buf = clientsocket.recv(MAX_LENGTH)
            if buf != b'':
                self.received=buf
                self.data = self.received.decode("utf-8").split(";") #[to_snap,exp,cycle,step]
            time.sleep(0.05)

class Pipe_Syntax(Thread):

    def __init__(self,namedPipe_path):
        Thread.__init__(self,daemon=True)

        self.namedPipe_path=namedPipe_path
        self.received=b""
        self.data=[]
        if (not os.path.exists(self.namedPipe_path)):
            os.mkfifo(self.namedPipe_path)

    def run(self):
        self.run_name = "test_nofull"
        with open(self.namedPipe_path,'r') as fifo:
            try:
                if is_384:
                    print("384 run")
                    self.run_name = fifo.read().strip().replace(" ", "_").replace("/", "-")
            except Exception as e:
                print("Couldn't take snapshot...", e)

        print("Run: ", self.run_name)

        while(1):
            with open(self.namedPipe_path,'r') as fifo:
                try:
                    if is_384:
                        self.received = fifo.read().strip().split('-')
                        print(self.received)
                        cycle=self.received[0].split('/')[0].replace('Cycle ','')
                        if not cycle.isnumeric():
                            cycle='0'
                        step = self.received[1].replace('/', '_') + "_" + self.received[2]
                        print(step)
                        self.data=[1,self.run_name,cycle,step]
                    else:
                        self.received = fifo.read().strip().split('\n')[-1] #sometimes two json were passed to the named pipe, had to take the last one
                        print(self.received)
                        data_json=json.loads(self.received)
                        self.data=[1,"STX_run",data_json['cycle'],data_json['step']] #[to_snap,exp,cycle,step]
                except Exception as e:
                    print("Couldn't take snapshot...", e)

if __name__ == "__main__":
    pipe_server=Pipe_Syntax("/tmp/thermal-monitor")
    pipe_server.start()
