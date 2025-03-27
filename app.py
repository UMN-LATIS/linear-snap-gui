import wx
from gui import MyGui
import multiprocessing
import sys
from PyQt5.QtWidgets import (QFileDialog, QAbstractItemView, QListView,
							 QTreeView, QApplication, QDialog)
if __name__ == "__main__":
	multiprocessing.freeze_support()


class CustomOutputWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "LinearSnap Output", 
                          pos=(50, 50), size=(600, 300))
        self.text = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY)
        
    def write(self, text):
        self.text.AppendText(text)

class MyApp(wx.App):
	def OnInit(self):
		self.outputWindow = CustomOutputWindow()
		self.outputWindow.Show()
		sys.stdout = self.outputWindow
		sys.stderr = self.outputWindow
		frame = MyGui(None)
		self.SetTopWindow(frame)
		frame.Show(True)
		
		return True

qapp = QApplication(sys.argv)
app = MyApp(True)
app.MainLoop()


