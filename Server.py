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

svr = "[SERVER]: "

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
        print("To close server, please use Ctrl + c")
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
    client.send(bytes(svr + "Enter usernaname: ", "utf8"))
    name = client.recv(BUFFSIZE).decode("utf8").strip()
    # Check username
    while name not in creds or inonline(name):
        if name not in creds:
            client.send(bytes(svr + "Username not in database\n", "utf8"))  
        elif inonline(name):
            client.send(bytes(svr + "User already logged in\n", "utf8"))
        client.send(bytes(svr + "Enter usernaname: ", "utf8"))
        name = client.recv(BUFFSIZE).decode("utf8").strip()
    
    if clients[name].isblockout():
        client.send(bytes(svr + "You are blocked out ", "utf8"))
        buffer.sleep(1)
        client.send(bytes("[logout]", "utf8"))
        client.close()
        return

    # Check password
    client.send(bytes(svr + "Enter password: ", "utf8"))
    password = client.recv(BUFFSIZE).decode("utf8").strip()
    while creds[name] != password:
        passwordCheck += 1
        if passwordCheck == 3:
            client.send(bytes(svr + f"You are blocked out for {BLOCKOUT} seconds", "utf8"))
            buffer.sleep(1)
            clients[name].setblockout(datetime.now().timestamp())
            client.send(bytes("[logout]", "utf8"))
            client.close()
            return
        client.send(bytes(svr + "Incorrect password, try again\n", "utf8"))
        client.send(bytes(svr + "Enter password: ", "utf8"))
        password = client.recv(BUFFSIZE).decode("utf8").strip()

    # Client has logged in
    onlineClients[client] = name
    clients[name].setlastLogged(datetime.now().timestamp())
    client.send(bytes(f"[yourName] {name}", "utf8"))
    buffer.sleep(0.1)

    # Send welcome msg upon success
    welcome = svr +  f"Welcome {name} to the *cough* 'greatest' messaging application ever!\n" 
    client.send(bytes(welcome, "utf8"))

    # Send any stored messages
    for msg in clients[name].getstoredmsg():
        client.send(bytes(msg + "\n", "utf8"))
    clients[name].clearstoredmsg()

    # Broadcast login to all online users
    presense = f"*{name}* has joined the server"
    broadcast(presense, "SERVER", client)

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
            broadcast(logout, "SERVER", client)
            client.send(bytes("[logout]", "utf8"))
            clients[name].setlastLogged(datetime.now().timestamp())
            client.close()
            del addresses[client]
            del onlineClients[client]

            break 
        # MESSAGE
        elif msgComd == "message":
            if len(recv.split(None, -1)) < 3:
                client.send(bytes(svr + "Usage: massage <user> <message>", "utf8"))
            else:
                recvName = recv.split(None, 2)[1].strip()
                msg = recv.split(None, 2)[2].strip()
                if isBlocked(recvName, name):
                    client.send(bytes(svr + "Couldn't send message to " + recvName, "utf8"))
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
                client.send(bytes(svr + "Usage: whoelsesince <time>", "utf8"))
            else:
                time = int(recv.split(None, 1)[1].strip())
                onlineTime = getWhoElseTime(name, time)
                client.send(bytes(onlineTime, "utf8"))
        # BLOCK
        elif msgComd == "block":
            if len(recv.split(None, -1)) < 2:
                client.send(bytes(svr + "Usage: block <user>", "utf8"))
            else:
                blockname = recv.split(None, 2)[1].strip()
                if blockname not in clients:
                    client.send(bytes(svr + "User not found", "utf8"))
                elif blockname == name:
                    client.send(bytes(svr + "Cannot block self", "utf8"))
                else:
                    if clients[name].addblacklist(blockname):
                        client.send(bytes(svr + f"Successfully blocked *{blockname}*", "utf8"))
                    else:
                        client.send(bytes(svr + f"*{blockname}* already blocked", "utf8"))
        # UNBLOCK
        elif msgComd == "unblock":
            if len(recv.split(None, -1)) < 2:
                client.send(bytes(svr + "Usage: unblock <user>", "utf8"))
            else:
                blockname = recv.split(None, 2)[1].strip()
                if blockname not in clients:
                    client.send(bytes(svr + "User not found", "utf8"))
                elif blockname == name:
                    client.send(bytes(svr + "Cannot unblock self", "utf8"))
                else:
                    if clients[name].removeblacklist(blockname):
                        client.send(bytes(svr + f"Successfully unblocked *{blockname}*", "utf8"))
                    else:
                        client.send(bytes(svr + f"*{blockname}* was not blocked", "utf8"))
        # START P2P
        elif msgComd == "startprivate":
            if len(recv.split(None, -1)) < 2:
                client.send(bytes(svr + "Usage: startprivate <user>", "utf8"))
            else:
                user = recv.split(None, 2)[1].strip()
                startPrivate(user, client)
        else:
            client.send(bytes(svr + "Error. Invalid Command", "utf8"))

# Server functions -----------------------------------------------

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
            onlineMembers += svr + onlineClients[client] + "\n"
    
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
        if inonline(client) or timeOnline < duration:
            mem = svr + clients[client].getname() + "\n"
            onlineMembers += mem

    return onlineMembers

def broadcast(msg, name="", thisClient= None):
    thisClientName = onlineClients[thisClient]
    for client in onlineClients:
        recvName = onlineClients[client]
        if name == "SERVER":
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
    thisClientName = onlineClients[thisClient]
    if name == thisClientName:
            thisClient.send(bytes(svr + f"Can't connect to {name} as this user is YOU", "utf8"))   
            return
    for client in onlineClients:
        if onlineClients[client] == name:
            if isBlocked(name, thisClientName):
                thisClient.send(bytes(svr + f"Can't connect to {name} as this user has blocked you", "utf8"))
            else:
                addr = addresses[client]
                thisClient.send(bytes(f"[IP,PORT] {name} {addr}", "utf8"))
            return
    # End of for loop with no return impliess user not online
    thisClient.send(bytes(svr + f"Can't connect to {name} as this user is offline or does not exist", "utf8"))    

def inonline(name):
    for client in onlineClients:
        if name == onlineClients[client]:
            return True
    return False


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
                            client.send(bytes(svr + "You have timed out", "utf8"))
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
