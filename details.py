class ClientDetails():
    name = ""
    blockout = None
    timeout = None
    lastLogged = None
    blacklist = []
    storedMsg = []
    def __init__(self, name, blockout, timeout, lastlogged, blacklist, storedMsg):
        self.name = name
        self.blockout = blockout
        self.timeout = timeout
        self.lastLogged = lastlogged
        self.blacklist = blacklist
        self.storedMsg = storedMsg
    # NAME
    def getname(self):
        return self.name

    # BLOCKOUT
    def getblockout(self):
        return self.blockout

    def isblockout(self):
        return self.blockout != None

    def removeBlockout(self):
        self.blockout = None

    def setblockout(self, blockout):
        self.blockout = blockout
    
    # TIMEOUT
    def gettimeout(self):
        return self.timeout

    def hastimeout(self):
        return self.timeout != None

    def removeTimeout(self):
        self.timeout = None

    def settimeout(self, timeout):
        self.timeout = timeout

    # LAST LOGGED
    def getlastLogged(self):
        return self.lastLogged

    def setlastLogged(self, lastLogged):
        self.lastLogged = lastLogged

    # BLACKLIST
    def getblacklist(self):
        return self.blacklist

    def addblacklist(self, name):
        self.blacklist.append(name)

    def removeblacklist(self, name):
        self.blacklist.remove(name)

    # STORED MESSAGES
    def getstoredmsg(self):
        return self.storedMsg

    def addstoredmsg(self, msg):
        self.storedMsg.append(msg)

    def clearstoredmsg(self):
        self.storedMsg.clear()

