import wx
from gui import MyGui
import multiprocessing

if __name__ == "__main__":
	multiprocessing.freeze_support()

class MyApp(wx.App):
	def OnInit(self):
		frame = MyGui(None)
		self.SetTopWindow(frame)
		frame.Show(True)
		
		return True


app = MyApp(True)
app.MainLoop()


