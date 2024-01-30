import wx
# import serial
import time
import threading
from LinearSnapFrame import LinearSnapFrame
from LinearSnapControl import LinearSnapControl
from CameraControl import CameraControl
import cv2
from pubsub import pub
from config import LSConfig;
from Preferences import PreferencesEditor;

class MyGui(LinearSnapFrame):
	
	
	app = wx.App(0)
	
	def __init__(self, parent):
		self.config = LSConfig()
		self.controller =  LinearSnapControl(self.config);
		self.camera = CameraControl(self.config);
		LinearSnapFrame.__init__(self, parent)
		
		self.m_EnableLiveView.Bind( wx.EVT_CHECKBOX, self.liveView )
		self.timer = wx.Timer(self)
		self.timer.Start(int(1000. / 15.))
		
		self.m_LiveView.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_TIMER, self.NextFrame)

		# Create the menubar
		menuBar = wx.MenuBar()

		self.SetMenuBar(menuBar)
		self.Bind(wx.EVT_CLOSE, self.onExitButton)

		pub.subscribe(self.coreStatus, "coreStatus")

	def onExitButton(self, event):
		self.controller.stopRail("S")
		self.controller.stopRail("L")
		self.controller.triggerHalt()
		self.camera.stopWaiting = True
		self.timer.Stop()
		quit()

	def coreStatus(self, message):
		if(message == "end"):
			self.coreCompleteText.Show()
			self.Layout()

			# need to run on main thread
			# wx.CallAfter(self.m_coreId.SetValue, "")
			timer = threading.Timer(6,lambda : self.coreCompleteText.Hide())
			timer.start()
			self.controller.moveRail("S", 1, 50);
			print("Core Complete")
			self.camera.notifyCoreComplete()
			time.sleep(3)
			self.controller.goHome()

	def moveShortBack(self, event):
		print("Moving Short Back")
		if(self.m_SlowMoves.GetValue() == True):
			self.controller.moveRail("S", 0, 1);
		else:
			self.controller.runRail("S", "0")

	def moveShortForward( self, event ):
		print("Moving Short Forward")
		if(self.m_SlowMoves.GetValue() == True):
			self.controller.moveRail("S", 1, 1);
		else:
			self.controller.runRail("S", 1)

	def stopShort( self, event ):
		self.controller.stopRail("S")

	def moveLongLeft( self, event ):
		print("Moving Long Left")
		if(self.m_SlowMoves.GetValue() == True):
			self.controller.moveRail("L", 1, 1);
		else:
			self.controller.runRail("L", 1)

	def moveLongRight( self, event ):
		print("Moving Long Right")
		if(self.m_SlowMoves.GetValue() == True):
			self.controller.moveRail("L", 0, 1);	
		else:
			self.controller.runRail("L", 0)

	def stopLong( self, event ):
		self.controller.stopRail("L")

	def goHome( self, event ):
		self.controller.goHome()

	def stopAll( self, event ):
		self.controller.stopRail("S")
		self.controller.stopRail("L")
		self.controller.triggerHalt()
		self.camera.setLiveView(False)
		self.camera.stopWaiting = True
		

	def coreComplete(self):
		print("Core Complete")

	def findFocus(self, event):
		print("Finding Focus")
		t = threading.Thread(target=self.controller.findInitialFocus,
								args=(self.camera,), name='focus-worker')
		t.daemon = True
		t.start()

	def imageCore( self, event ):
		print("Start")
		if(self.m_coreId.GetValue() == ""):
			wx.MessageBox('You must specify a core name', 'Error', wx.OK | wx.ICON_WARNING)
			return



		t = threading.Thread(target=self.controller.imageCore,
								args=(self.m_coreId.GetValue(), self.coreComplete, self.camera,self.m_coreType.GetString(self.m_coreType.GetCurrentSelection())), name='core-worker')
		t.daemon = True
		t.start()
		# self.controller.imageCore(self.coreComplete)	

	def liveView(self, event):
		self.camera.setLiveView(self.m_EnableLiveView.GetValue())

	def OnPaint(self, event):
		self.m_ShortRail.SetLabel(str(self.controller.railPosition["S"]))
		self.m_LongRail.SetLabel(str(self.controller.railPosition["L"]))
		self.m_PhotoCount.SetLabel(str(self.camera.photoCount))
		self.m_PositionCount.SetLabel(str(self.controller.positionCount))
		if self.camera.image is not None:
			dc = wx.BufferedPaintDC(self.m_LiveView)
			dc.Clear()
			width, height = self.m_LiveView.GetSize()
			aspect_ratio = self.camera.image.shape[1] / self.camera.image.shape[0]
			if width / height > aspect_ratio:
				width = int(height * aspect_ratio)
			else:
				height = int(width / aspect_ratio)
			resized = cv2.resize(self.camera.image, (width, height))
			recolored = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
			dc.DrawBitmap(wx.Bitmap.FromBuffer(recolored.shape[1], recolored.shape[0], recolored), 0, 0)
			self.m_Focus.SetLabel("{:.2f}".format(self.camera.laplacian))
			
	
	def NextFrame(self, event):
		self.Refresh()

	def OnTimer(self, evt):
		self.drawFrame()

	def openPrefs( self, event ):
		self.prefs = PreferencesEditor(self.config)
		self.prefs.Show(self)


	def changeCoreType( self, event ):
		self.config.configValues['CoreType'] = str(self.m_coreType.GetCurrentSelection())
		self.config.save_config()