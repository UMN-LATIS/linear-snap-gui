import wx
# import serial
import time
import threading
from miniMacroFrame import MiniMacroFrame
from miniMacroControl import miniMacroControl
from CameraControl import CameraControl
import cv2
class MyGui(MiniMacroFrame):
	
	
	app = wx.App(0)
	
	def __init__(self, parent):
		self.controller =  miniMacroControl();
		self.camera = CameraControl();
		MiniMacroFrame.__init__(self, parent)

	def moveShortBack(self, event):
		print("Moving Short Back")
		if(self.m_checkBox2.GetValue() == True):
			self.controller.moveRail("S", 0, 1);
		else:
			self.controller.runRail("S", "0")

	def moveShortForward( self, event ):
		print("Moving Short Forward")
		if(self.m_checkBox2.GetValue() == True):
			self.controller.moveRail("S", 1, 1);
		else:
			self.controller.runRail("S", 1)

	def stopShort( self, event ):
		print("Stop")
		self.controller.stopRail("S")

	def moveLongLeft( self, event ):
		print("Moving Long Left")
		if(self.m_checkBox2.GetValue() == True):
			self.controller.moveRail("L", 1, 1);
		else:
			self.controller.runRail("L", 1)

	def moveLongRight( self, event ):
		print("Moving Long Right")
		if(self.m_checkBox2.GetValue() == True):
			self.controller.moveRail("L", 0, 1);	
		else:
			self.controller.runRail("L", 0)

	def stopLong( self, event ):
		self.controller.stopRail("L")

	def goHome( self, event ):
		self.controller.goHome()

	def findFocus( self, event ):
		self.controller.findFocus()

	def stopAll( self, event ):
		self.controller.stopRail("S")
		self.controller.stopRail("L")
		self.controller.halt()

	def coreComplete(self):
		print("Core Complete")


	def imageCore( self, event ):
		print("Start")
		t = threading.Thread(target=self.camera.waitForPhoto,
								args=(self.m_textCtrl3.GetValue(),), name='camera-worker')
		t.daemon = True
		t.start()
		t = threading.Thread(target=self.controller.imageCore,
								args=(self.m_textCtrl3.GetValue(), self.coreComplete,), name='core-worker')
		t.daemon = True
		t.start()
		# self.controller.imageCore(self.coreComplete)	

	def liveView(self, event):
		self.camera.setLiveView(self.m_checkBox1.GetValue())

	def OnPaint(self, event):
		if self.camera.image is not None:
			dc = wx.BufferedPaintDC(self.m_panel1)
			dc.Clear()
			width, height = self.m_panel1.GetSize()
			aspect_ratio = self.camera.image.shape[1] / self.camera.image.shape[0]
			if width / height > aspect_ratio:
				width = int(height * aspect_ratio)
			else:
				height = int(width / aspect_ratio)
			resized = cv2.resize(self.camera.image, (width, height))
			recolored = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
			dc.DrawBitmap(wx.Bitmap.FromBuffer(recolored.shape[1], recolored.shape[0], recolored), 0, 0)
			self.m_staticText31.SetLabel("{:.2f}".format(self.camera.laplacian))
			self.m_staticText6.SetLabel(self.controller.railPosition["S"])
			self.m_staticText8.SetLabel(self.controller.railPosition["L"])
			self.m_staticText10.SetLabel(self.camera.photoCount)
			self.m_staticText12.SetLabel(self.controller.positionCount)
	
	def NextFrame(self, event):
		self.Refresh()

	def OnTimer(self, evt):
		self.drawFrame()
