import wx
import client
import server

app = wx.App()
server = server.serverFrame(None)
client = client.client(None)
app.MainLoop()