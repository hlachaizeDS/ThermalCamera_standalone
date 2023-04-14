import socket
import sys


HOST = '127.0.0.1'
PORT = 10000
s = socket.socket()
s.connect((HOST, PORT))

str_to_pass=""
for arg in sys.argv[1:]:
    str_to_pass += ";" + arg

str_to_pass=str_to_pass[1:]

msg = bytes(str_to_pass, 'utf-8')

s.send(msg)
s.close()