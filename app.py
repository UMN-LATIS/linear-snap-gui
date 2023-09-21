import wx
from gui import MyGui
import multiprocessing
import sys
from PyQt5.QtWidgets import (QFileDialog, QAbstractItemView, QListView,
							 QTreeView, QApplication, QDialog)
if __name__ == "__main__":
	multiprocessing.freeze_support()

class MyApp(wx.App):
	def OnInit(self):
		frame = MyGui(None)
		self.SetTopWindow(frame)
		frame.Show(True)
		
		return True

qapp = QApplication(sys.argv)
app = MyApp(True)
app.MainLoop()


