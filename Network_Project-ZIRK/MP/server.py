import wx
import sys
import socket
import time
import threading
from threading import Thread
import select

class serverFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(serverFrame, self).__init__(*args, **kwargs)
        self.initialize()
    
    def initialize(self):
        # ~AESTHETICS~
        self.SetSize(315,500)
        self.mainPanel = wx.Panel(self)
        self.mainFont = wx.Font(20,wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.SetBackgroundColour("WHITE")
        self.defaultLog = "***************SERVER LOG****************\n"

        # ADD HEADER PHOTO
        imgHeader = wx.Image("rsrcs/header2_1.jpg", wx.BITMAP_TYPE_ANY).Scale(315,130)
        imgHeader = wx.Bitmap(imgHeader)
        self.header = wx.StaticBitmap(self.mainPanel, -1, imgHeader, (0,0), (315,130))

        # ADD SERVER BUTTON (OFF)
        imgServer = wx.Image("rsrcs/serverButton-1.jpg", wx.BITMAP_TYPE_ANY).Scale(60,60)
        imgServer = wx.Bitmap(imgServer)
        self.btnServer = wx.BitmapButton(self.mainPanel, -1, imgServer, (20,130),(60,60))
        self.btnServer.Bind(wx.EVT_BUTTON,self.startServer)

        # ADD QUIT BUTTON
        imgServer = wx.Image("rsrcs/quitButton.jpg", wx.BITMAP_TYPE_ANY).Scale(30,30)
        imgServer = wx.Bitmap(imgServer)
        self.btnQuit = wx.BitmapButton(self.mainPanel, -1, imgServer, (80,130),(30,30))
        self.btnQuit.Bind(wx.EVT_BUTTON, self.Quit)

        # ADD CLEAR BUTTON
        imgServer = wx.Image("rsrcs/clearButton.jpg", wx.BITMAP_TYPE_ANY).Scale(30,30)
        imgServer = wx.Bitmap(imgServer)
        self.btnClear = wx.BitmapButton(self.mainPanel, -1, imgServer, (80,160),(30,30))
        self.btnClear.Bind(wx.EVT_BUTTON, self.Clear)

        # ADD PREFERRED BUTTON
        imgServer = wx.Image("rsrcs/savePreferences.jpg", wx.BITMAP_TYPE_ANY).Scale(30,30)
        imgServer = wx.Bitmap(imgServer)
        self.preferredButton = wx.BitmapButton(self.mainPanel, -1, imgServer, (110,130),(30,30))
        self.preferredButton.Bind(wx.EVT_BUTTON, self.setPreferredPort)

        # INITIALIZE LOG AS UNEDITABLE TEXT FIELD
        self.log = wx.TextCtrl(self.mainPanel, style = wx.TE_READONLY | wx.TE_MULTILINE, pos=(0,200), size=(300,270))
        self.log.SetValue(self.defaultLog)
        
        self.SetTitle("Main Server")
        self.Center()
        self.Show()

    def setPreferredPort(self, e):
        portBox = wx.TextEntryDialog(None, "Type selected port", "Port Preferrence", '')
        if portBox.ShowModal() == wx.ID_OK:
            file = open("preferredPort.txt", "w")
            file.write(portBox.GetValue())
            file.close()
        
    def Quit(self, e):
        # EXITS APP
        self.Close()
        sys.exit()

    def Clear(self, e):
        # CLEARS LOG
        self.log.SetValue(self.defaultLog)
        self.Refresh()
        
    def startServer (self,e):
        file = open("preferredPort.txt", "r")
        temp = file.readline()
        
        if temp!= '':
            self.port = int(temp)
            file.close()
        else:
            portBox = wx.TextEntryDialog(None, "Start server on which port?", "Port Selection", '')
            if portBox.ShowModal() == wx.ID_OK:
                self.port = int(portBox.GetValue())

        # SERVER SHIT
        self.host = '127.0.0.1'

        # MAPS ADDRESS TO NAME
        self.clients={}
        # MAPS ADDRESS TO PORT
        self.addresses={}
        # MAPS GROUP TO NAMES
        self.groups = {}
        # MAPS ADDRESS TO GROUP NAME
        self.groupchats = {}
        # MAPS CHATROOM NAME TO PASSWORD AND USERS IN CHATROOM
        self.chatRooms = {}


        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        success= False

        # ATTEMPTS BINDING TO PORT
        try:
            self.s.bind((self.host,self.port))
            self.log.SetBackgroundColour((148,255,106))
            success=True
            self.log.AppendText("SERVER STARTING ON PORT " + str(self.port) + "\n")
        except:
            self.log.AppendText("PORT " + str(self.port) + " IS TAKEN, UNABLE TO START SERVER\n")

        # STARTS SERVER IF PORT IS NOT TAKEN
        if (success):
            self.quitting = False

            # ACTIVATE LISTENING THREAD
            self.s.listen(100)
            self.lT = threading.Thread(target=self.listening)
            self.lT.setDaemon(True)
            self.lT.start()

            # HIDE SERVER (OFF) BUTTON
            self.btnServer.Hide()
            self.preferredButton.Hide()

            # ADD SERVER BUTTON (ON)
            imgServer = wx.Image("rsrcs/serverButton-2.jpg", wx.BITMAP_TYPE_ANY).Scale(60,60)
            imgServer = wx.Bitmap(imgServer)
            self.btnServer2 = wx.BitmapButton(self.mainPanel, -1, imgServer, (20,130),(60,60))
            self.btnServer2.Bind(wx.EVT_BUTTON, self.stopServer)
        
            self.Refresh()

    # HANDLES A SINGLE CLIENT CONNECTION
    def handle_client(self,client): 
        while not self.quitting:
            msg = client.recv(1024)
            msg = msg.decode()
            print("BE ")
            silent = 0

            # CASE: NEW CLIENT CONNECTS
            if "@@connected"  in msg and " -> " not in msg:
                name = msg.split("@@connected ")[1]
                print("NAME IS: "+ name)

                # IF GROUP CHAT SENT CONNECTION REQUEST, ADD TO GROUPCHATS DICT
                if "Group" in name:
                    silent = 1
                    self.groupchats[client] = name
                else:
                    self.clients[client] = name
                    receiver = "Global"
                    msg = name + " has joined Zirk chat"
            # CASE: NEW CLIENT WANTS TO INITIALIZE LIST OF ACTIVE USERS
            elif "@@initlist " in msg and " -> " not in msg:
                name = msg.split("@@initlist ")[1]
                receiver = name
                #print(name + "MY NAME IS HERE")
                if "Group" in name:
                    silent = 1
                    msg = "@@initlist" 
                    for group in self.groupchats:
                        if name in self.groupchats[group]:
                            print("HER BEST")
                            for member in self.groups[name]:
                                print("FRIEND ONLY")
                                msg = msg + " " + member
                    group.send(msg.encode())
                                #print("MESSAGE SENT TO INITIALIZE GROUP CHAT: " + name + " MEMBER " + member)
                else:
                    msg = "@@initlist "
            # CASE: CLIENT SENDS FILE
            elif "sendfile@@" in msg:
                name = msg.split(" -> ")[0]
                receiver = msg.split(":")[0].split(" -> ")[1]
                filename = msg.split("@@")[1]
                filesize = msg.split("@@")[2]

                # SENDS INITIAL MSG TO RECEIVERS TO PREPARE FOR FILE DOWNLOAD
                msg = "sendfile@@"+filename+"@@"+filesize
                self.broadcast(msg, name, receiver)

                # SERVER MAKES OWN COPY OF FILE BEFORE SENDING PACKETS TO RECEIVERS
                # WRITE SERVER COPY OF FILE
                filesize = float(filesize)
                f = open("SERVER-COPY_"+filename, 'wb')
                toWrite = client.recv(1024)
                totalRecv = len(toWrite)
                f.write(toWrite)
                while totalRecv < filesize:
                    toWrite = client.recv(1024)
                    totalRecv += len(toWrite)
                    f.write(toWrite)
                    print("{0:.2f}".format((totalRecv/float(filesize)) * 100) + "percent done: SERVER SIDE")

                print("[-] File downloaded from client to server, file closed")
                f.close()
                print("[-] File closed, now sending to recipients")

                # SERVER NOW SENDS FILE TO RECEIVERS BY READING AND SENDING PER KILOBYTE
                with open("SERVER-COPY_"+filename, 'rb') as file:
                    bytesToSend = file.read(1024)
                    while bytesToSend:
                        if receiver == "Global":
                            for client in self.clients:
                                client.send(bytesToSend)
                        else:
                            for client in self.clients:
                                if (self.clients[client] == receiver or self.clients[client] == name):
                                    client.send(bytesToSend)
                        bytesToSend = file.read(1024)

                print("[-] Server done sending file to clients")
                silent= 1
            # CASE: GROUP CHAT
            elif "@@creategrp" in msg:
                names = msg.split("@@")[2].split(",")
                groupName = "Group " + str(len(self.groups)+1)
                self.groups[groupName] = names
                print(self.groups)
                msg = names[0] + " Created group chat with you @@" + str(self.port) +"@@"+groupName

                # TELL EVERY SELECTED USER TO OPEN GROUPCHAT TAB
                for temp in names:
                    for client in self.clients:
                        if (self.clients[client] == temp):
                            client.send(msg.encode())
                            time.sleep(.2)
 
                silent = 1
            # CASE: CREATING CHAT ROOM (the one with password)
            elif "@@addCR@@" in msg and "->" not in msg:
                error = False
                owner = msg.split("@@")[0]
                
                groupname = msg.split("@@")[2]
                grouppass = msg.split("@@")[3]
                for x in self.chatRooms.keys():
                    if x is groupname:
                        error = True
                if error is True:
                    self.broadcast("ERROR in creating Chat Room with name " + groupname, owner, owner)
                else:
                    self.chatRooms[groupname] = [grouppass, []]
                    self.chatRooms[groupname][1].append(owner)
                    msg = owner + " Created chat room @@" + str(self.port) + "@@"+ groupname 
                    self.broadcast(msg, owner, "Global")
                silent = 1
            # CASE: NORMAL MESSAGE
            elif " -> " in msg:
                name = msg.split(" -> ")[0]
                receiver = msg.split(" -> ")[1].split(": ")[0]

            # UPDATE SERVER LOG
            if not silent:
                self.log.AppendText(time.ctime(time.time()) + str(self.addresses[client]) + ": :" + str(msg) + "\n")

            # CASE: CLIENT DISCONNECTS FROM GROUP
            if "@@disconnectedFromGroup" in msg and " -> " not in msg:
                client.close()
                name = msg.split(" ")[1] 
                receiver = msg.split(" ")[2] + " " + msg.split(" ")[3]
                address = receiver + ":" + name
                print(address)
                msg = name + " has disconnected"
                self.groups[receiver].remove(name)
                for group in self.groupchats:
                    if (self.groupchats[group] == address):
                        print(self.groupchats[group] + " HORY SHIT HERE IT IS")
                        del self.groupchats[group]
                        break
                print(self.groups)
                print(self.groupchats)
                self.multicast(msg, receiver)
                break
            # CASE: CLIENT DISCONNECTS
            elif "@@disconnected" in msg and " -> " not in msg:
                client.close()
                name = msg.split("@@disconnected ")[1]
                receiver = "Global"
                msg = name + " has disconnected"
                for client in self.clients:
                    if (self.clients[client] == name):
                        del self.clients[client]
                        del self.addresses[client]
                        break
                print("ABOUT TO ENTER")
                # TEMPORARY DICTIONARY TO HOLD NEW LIST OF USERS PER GROUP
                tempdict = {}
                for group in self.groupchats:
                    print("ENTERED")
                    print(group)
                    address = ""
                    for member in self.groups[self.groupchats[group].split(":")[0]]:
                        print(member + " HERE")
                        if member == name:
                            address = self.groupchats[group]
                            print(address)
                            self.groups[self.groupchats[group].split(":")[0]].remove(name)
                            print(self.groupchats[group] + " HERE WE GO")
                            print(self.groups[self.groupchats[group].split(":")[0]])
                        elif member != name:
                            tempdict[group] = self.groupchats[group]
                self.groupchats = tempdict
                for group in self.groups:
                    self.multicast(msg,group)
                    
                print(tempdict)
                print(self.groups)
                print(self.groupchats)
                self.broadcast(msg, name, receiver)
                break

            if not silent:
                # NORMAL CHAT (PRIVATE OR GLOBAL)
                if "Group" not in receiver:
                    self.broadcast(msg, name, receiver)
                # MULTICAST (GROUPCHAT)
                else:
                    self.multicast(msg, receiver)

    # FUNCTION TO HANDLE PROPER SENDING OF MSG TO APPROPRIATE RECEIVERS
    def broadcast(self, msg, name, receiver):
        print("SENDER: " + name)
        print("RECEIVER: " + receiver)

        if receiver == "Global":
            for client in self.clients:
                client.send(msg.encode())
                print("MSG SENT FROM SERVER TO GLOBAL")
        else:
            if "@@initlist " in msg and " -> " not in msg:
                for client in self.clients:
                    if (self.clients[client] == receiver or self.clients[client] == name):
                        for i in self.clients:
                            client.send((msg + self.clients[i]).encode())
                            print(str(msg) + " SENT FROM SERVER")
                            time.sleep(.1)
                        break
            else:
                for client in self.clients:
                    if (self.clients[client] == receiver or self.clients[client] == name):
                        client.send(msg.encode())
                        print(str(msg) + " SENT FROM SERVER")

    # FUNCTION TO HANDLE PROPER SENDING OF MSG TO APPROPRIATE GROUPCHATS
    def multicast(self, msg, receiver):
        for group in self.groupchats:
            if receiver in self.groupchats[group]:
                group.send(msg.encode())
                print("MESSAGE SENT TO GROUP CHAT: " + receiver)
        
    # THREAD TO LISTEN TO INCOMING CONNECTIONS
    def listening(self):
        while not self.quitting:
            client_address, port = self.s.accept()
            self.addresses[client_address] = port
            Thread(target=self.handle_client, args=(client_address,)).start()

    def stopServer(self,e):
        # HIDES AND SHOWS APPROPRIATE BUTTONS
        self.btnServer.Show()
        self.btnServer2.Hide()
        self.preferredButton.Show()

        # SHUTS SERVER DOWN, CLOSES THREAD
        self.quitting = True
        self.s.close()

        self.log.SetBackgroundColour((255,255,255))
        self.log.AppendText("SERVER TERMINATING...\n")
        self.Refresh()

def main():
    app = wx.App()
    serverFrame(None)
    app.MainLoop()
