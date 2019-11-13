# Using Python 3
from socket import *
import select
import sys
from threading import Thread 
from details import ClientDetails
from datetime import *
import time

if len(sys.argv) != 4:
    print("Usage: Server.py PORT BLOCK TIMEOUT")
    exit()

PORT = int(sys.argv[1])
IP = 'localhost'
ADDR = (IP, PORT)

BUFFSIZE = 1024
BLOCKOUT = int(sys.argv[2])
TIMEOUT = int(sys.argv[3])

buffer = time

clients = {}
onlineClients = {}
addresses = {}
creds = {}
f = open("credentials.txt", "r")    
for line in f:
    username = line.split(None, 1)[0]
    userPassword = line.split(None, 1)[1].strip()
    creds[username] = userPassword
    if username not in clients:
        clientdets = ClientDetails(username, None, None, None, [], [])
        clients[username] = clientdets

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)

serverSocket.bind(ADDR)

def accept_connections():
    Thread(target=activateClock).start()
    
    while True:
        print("waiting for clients")
        client, clientAddr = serverSocket.accept()
        print(f"{clientAddr} has connected")

        cServerAddr = client.recv(BUFFSIZE).decode("utf8").strip()

        print(cServerAddr)
        addresses[client] = cServerAddr
        
        Thread(target=handleConnection, args=(client,)).start()
    

def handleConnection(client):
    
    # AUTHENTICATION--------------------------------------------------
    passwordCheck = 0

    # Prompt for username
    client.send(bytes("Enter usernaname: ", "utf8"))
    name = client.recv(BUFFSIZE).decode("utf8").strip()

    client.send(bytes(f"[yourName] {name}", "utf8"))
    buffer.sleep(0.1)

    # Check username
    while name not in creds:
        client.send(bytes("Username not in database\n", "utf8"))
        client.send(bytes("Enter usernaname: ", "utf8"))
        name = client.recv(BUFFSIZE).decode("utf8").strip()

    while name in onlineClients:
        client.send(bytes("User already logged in\n", "utf8"))
        client.send(bytes("Enter usernaname: ", "utf8"))
        name = client.recv(BUFFSIZE).decode("utf8").strip()
    
    if clients[name].isblockout():
        client.send(bytes("You are blocked out ", "utf8"))
        buffer.sleep(1)
        client.send(bytes("[logout]", "utf8"))
        client.close()
        return

    # Check password
    client.send(bytes("Enter password: ", "utf8"))
    password = client.recv(BUFFSIZE).decode("utf8").strip()
    while creds[name] != password:
        passwordCheck += 1
        if passwordCheck == 3:
            client.send(bytes(f"You are blocked out for {BLOCKOUT} seconds", "utf8"))
            buffer.sleep(1)
            clients[name].setblockout(datetime.now().timestamp())
            client.send(bytes("[logout]", "utf8"))
            client.close()
            return
        client.send(bytes("Incorrect password, try again\n", "utf8"))
        client.send(bytes("Enter password: ", "utf8"))
        password = client.recv(BUFFSIZE).decode("utf8").strip()

    # Client has logged in
    onlineClients[client] = name
    clients[name].setlastLogged(datetime.now().timestamp())

    # Send welcome msg upon success
    welcome = f"Welcome {name}!\n" 
    client.send(bytes(welcome, "utf8"))

    # Send any stored messages
    for msg in clients[name].getstoredmsg():
        client.send(bytes(msg + "\n", "utf8"))
    clients[name].clearstoredmsg()

    # Broadcast login to all online users
    presense = f"*{name}* has joined the server"
    broadcast(presense, "Server", client)

    # Set timeout
    clients[name].settimeout(datetime.now().timestamp())

    # CLIENT COMMANDS------------------------------------------------------
    while True:
        recv = client.recv(BUFFSIZE).decode("utf8").strip()

        if len(recv.split(None, 1)) == 0:
            break
        
        # Reset timeout
        clients[name].settimeout(datetime.now().timestamp())

        msgComd = recv.split(None, 1)[0].strip()
        
        # LOGOUT
        if msgComd == "logout":
            logout = f"*{name}* has logged out"
            broadcast(logout, "Server", client)
            client.send(bytes("[logout]", "utf8"))
            clients[name].setlastLogged(datetime.now().timestamp())
            client.close()
            del addresses[client]
            del onlineClients[client]

            break 
        # MESSAGE
        elif msgComd == "message":
            if len(recv.split(None, -1)) < 3:
                client.send(bytes("Usage: massage <user> <message>", "utf8"))
            else:
                recvName = recv.split(None, 2)[1].strip()
                msg = recv.split(None, 2)[2].strip()
                if isBlocked(recvName, name):
                    client.send(bytes("Couldn't send message to " + recvName, "utf8"))
                else:
                    personalmsg(recvName, msg, name)
        # BROADCAST
        elif msgComd == "broadcast":
            msg = recv.split(None, 1)[1].strip()
            broadcast(msg, name, client)
        # WHOELSE
        elif msgComd == "whoelse":
            online = getWhoElse(name)
            client.send(bytes(online, "utf8"))
        elif msgComd == "whoelsesince":
            if len(recv.split(None, -1)) < 2:
                client.send(bytes("Usage: whoelsesince <time>", "utf8"))
            else:
                time = int(recv.split(None, 1)[1].strip())
                onlineTime = getWhoElseTime(name, time)
                client.send(bytes(onlineTime, "utf8"))
        # BLOCK
        elif msgComd == "block":
            if len(recv.split(None, -1)) < 2:
                client.send(bytes("Usage: block <user>", "utf8"))
            else:
                blockname = recv.split(None, 2)[1].strip()
                if blockname not in clients or blockname == name:
                    client.send(bytes("User not found", "utf8"))
                else:
                    clients[name].addblacklist(blockname)
                    client.send(bytes(f"Successfully blocked *{blockname}*", "utf8"))
        # UNBLOCK
        elif msgComd == "unblock":
            if len(recv.split(None, -1)) < 2:
                client.send(bytes("Usage: unblock <user>", "utf8"))
            else:
                blockname = recv.split(None, 2)[1].strip()
                if blockname not in clients or blockname == name:
                    client.send(bytes("User not found", "utf8"))
                else:
                    clients[name].removeblacklist(blockname)
                    client.send(bytes(f"Successfully unblocked *{blockname}*", "utf8"))
        # START P2P
        elif msgComd == "startprivate":
            if len(recv.split(None, -1)) < 2:
                client.send(bytes("Usage: startprivate <user>", "utf8"))
            else:
                user = recv.split(None, 2)[1].strip()
                startPrivate(user, client)

        elif msgComd == "test":
            test()

# Server functions -----------------------------------------------
def test():
    for address in addresses:
        print(addresses[address])

def personalmsg(recvName, msg, sendName):
    for client in onlineClients:
        if onlineClients[client] == recvName:
            client.send(bytes("[" + sendName + "]: " + msg, "utf8"))
            return
    if recvName in clients:
        fullmsg = "[" + sendName + "]: " + msg
        clients[recvName].addstoredmsg(fullmsg)

def getWhoElse(thisName):
    onlineMembers = ""
    for client in onlineClients:
        clientName = onlineClients[client]
        if isBlocked(clientName, thisName):
            continue
        if clientName != thisName:
            onlineMembers += onlineClients[client] + "\n"
    
    return onlineMembers

def getWhoElseTime(thisName, duration):
    onlineMembers = ""
    now = datetime.now().timestamp()
    for client in clients:
        if isBlocked(client, thisName):
            continue
        if clients[client].getlastLogged() == None or clients[client].getname() == thisName:
            continue
        timeOnline = int(now - clients[client].getlastLogged())
        if timeOnline < duration:
            mem = "*" + clients[client].getname() + "* logged in " + str(timeOnline) + " seconds ago\n"
            onlineMembers += mem

    return onlineMembers

def broadcast(msg, name="", thisClient= None):
    thisClientName = onlineClients[thisClient]
    for client in onlineClients:
        recvName = onlineClients[client]
        if name == "Server":
            if recvName in clients[thisClientName].getblacklist():
                continue
        else:
            if isBlocked(recvName, thisClientName):
                continue
        if client != thisClient:   
            client.send(bytes("[" + name + "]: " + msg, "utf8"))
            

def isBlocked(recv, send):
    return send in clients[recv].getblacklist()

def startPrivate(name, thisClient):
    for client in onlineClients:
        if onlineClients[client] == name:
            addr = addresses[client]
            
            thisClient.send(bytes(f"[IP,PORT] {name} {addr}", "utf8"))

# CLOCK FOR TIMEOUT AND BLOCKOUT--------------------------------
def activateClock():
    while True:
        global clock_thread
        if clock_thread:
            break
        
        # Magic happens here
        for client in clients:
            now = datetime.now().timestamp()
            clientDets = clients[client]
            # Check Blockout
            if clientDets.isblockout():
                timeBlockout = int(now - clientDets.getblockout())
                if timeBlockout > BLOCKOUT:
                    clientDets.removeBlockout()
            # Check Timeout
            if clientDets.hastimeout():
                timeTimeout = int(now - clientDets.gettimeout())
                if timeTimeout > TIMEOUT:
                    for client in onlineClients:
                        if onlineClients[client] == clientDets.getname():
                            client.send(bytes("You have timed out", "utf8"))
                            buffer.sleep(1)
                            client.send(bytes("[logout]", "utf8"))
                            client.close
                            del addresses[client]
                            del onlineClients[client]
                            clientDets.removeTimeout()
                            break
                        
        buffer.sleep(1)

# MAIN----------------------------------------------------------------
if __name__ == "__main__":
    serverSocket.listen()
    print("Server listening...")
    try:
        clock_thread = False
        accept_thread = Thread(target=accept_connections())
        accept_thread.start()
        accept_thread.join()
    except KeyboardInterrupt:
        for client in onlineClients:
            client.send(bytes("[logout]", "utf8"))
        serverSocket.shutdown(SHUT_RDWR)
        serverSocket.close()
        clock_thread = True
        print("Server closed")
        exit()
