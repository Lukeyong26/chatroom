from socket import *
import select
import sys
from threading import Thread
import random

# ASK ABOUT P2P PORT
# ASK ABOUT P2P CONNECTION 2 WAY?

BUFFSIZE = 1024

client_socket = socket(AF_INET, SOCK_STREAM)
cServer_socket = socket(AF_INET, SOCK_STREAM)
p2pClients = {}

if len(sys.argv) != 2:
    print("Usage: Client.py PORT")
    exit()

IP = "localhost"
PORT = int(sys.argv[1])
ADDR = (IP, PORT)

SVRADDR = ('', 0)
cServer_socket.bind(SVRADDR)
SVRADDR = cServer_socket.getsockname()
cServer_socket.listen()

client_socket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
client_socket.connect(ADDR)

# Sends Server ADDR I'm listening on
client_socket.send(bytes(f"{SVRADDR[0]} {SVRADDR[1]}", "utf8"))
username = ""

readables = [sys.stdin, client_socket, cServer_socket]

while True:
   
    read, write, error = select.select(readables,[],[])

    for sock in read:
        # Implies message from Server
        if sock == client_socket:
            msg = sock.recv(BUFFSIZE).decode("utf8").strip()
            tag = msg.split(None, 1)[0].strip()

            if tag == "[yourName]":
                username = msg.split(None, 1)[1]
            # Implies user wants to logout
            elif tag == "[logout]":
                client_socket.shutdown(SHUT_RDWR)
                client_socket.close()
                exit()
            # Implies user seting up P2P connection
            elif tag == "[IP,PORT]":
                name = msg.split(None, 4)[1].strip()
                server_ip = msg.split(None, 4)[2].strip()
                server_port = msg.split(None, 4)[3].strip()
                TRGADDR = (server_ip, int(server_port))
                print(name + " " + server_ip + server_port)
                
                pteConn_socket = socket(AF_INET, SOCK_STREAM)
                pteConn_socket.connect(TRGADDR)
                pteConn_socket.send(bytes(f"{username}", "utf8"))

                p2pClients[name] = pteConn_socket
                readables.append(pteConn_socket)
            else:
                print(msg)
        # Implies Incoming private connection
        elif sock == cServer_socket:
            privateClient, pteClientAddr = cServer_socket.accept()
            readables.append(privateClient)
            pteClientName = privateClient.recv(BUFFSIZE).decode("utf8").strip()
            
            print(pteClientName)
        # Read from std in
        elif sock == sys.stdin:
            line = sys.stdin.readline()
            if line.split(None, 1)[0] == "private":
                user = line.split(None, 3)[1]
                msg = line.split(None, 3)[2]
                
                p2pClients[user].send(bytes(f"[{username} (private)]: " + msg, "utf8"))
            else:    
                client_socket.send(bytes(f"{line}", "utf8"))
        # Other sockets in the list (created by p2p connections)
        else:
            msg = sock.recv(BUFFSIZE).decode("utf8").strip()
            print("something" + msg)


            


            
