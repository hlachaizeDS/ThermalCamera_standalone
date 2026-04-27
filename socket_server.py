import os, time

from threading import Thread
import socket
import json

MAX_LENGTH = 4096

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
        self.run_name = "no_run_name"

    def run(self):

        while(1):

            with open(self.namedPipe_path,'r') as fifo:
                try:
                    # We retrieve the message sent by the Syntax, and split it by " - "
                    self.received = fifo.read().strip().split(' - ')

                    # If it is a snapshot request, the command contains two ' - ', else it should be the run name
                    if len(self.received) != 3:

                        # If it's a run name, we clean the elements that could mess up the path of the folder
                        self.run_name = self.received[0].replace(" ", "_").replace("/", "-")
                        print("Run: ", self.run_name)

                    else:

                        print(self.received)

                        cycle=self.received[0].split('/')[0].replace('Cycle ','')

                        if not cycle.isnumeric():
                            cycle = '0'

                        step = self.received[1].replace('/', '_') + "_" + self.received[2]

                        print(step)

                        self.data = [1,self.run_name,cycle,step]  # [to_snap,exp,cycle,step]

                except Exception as e:
                    print("Couldn't take snapshot...", e)

if __name__ == "__main__":

    pipe_server=Pipe_Syntax("/tmp/thermal-monitor")
    pipe_server.start()
