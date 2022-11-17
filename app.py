import wx
from gui import MyGui

class MyApp(wx.App):
	def OnInit(self):
		frame = MyGui(None)
		self.SetTopWindow(frame)
		frame.Show(True)
		
		return True


app = MyApp(True)
app.MainLoop()


