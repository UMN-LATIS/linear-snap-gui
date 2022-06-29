import wx
import serial
import time
from miniMacroFrame import MiniMacroFrame
from miniMacroControl import miniMacroControl

class MyGui(MiniMacroFrame):
	app = wx.App(0)
	controller =  miniMacroControl();

	def moveShortBack(self, event):
		self.controller.runRail("S", "1")

	def stopShort( self, event ):
		self.controller.stopRail("S")

	def moveLongLeft( self, event ):
		self.controller.runRail("L", "1")

	def stopLong( self, event ):
		self.controller.stopRail("L")

	def moveLongRight( self, event ):
		self.controller.runRail("L", "0")

	def moveShortForward( self, event ):
		self.controller.runRail("S", "0")

	def goHome( self, event ):
		self.controller.goHome()

	def findFocus( self, event ):
		self.controller.findFocus()

	def stopAll( self, event ):
		self.controller.stopRail("S")
		self.controller.stopRail("L")

	def coreComplete(self):
		print("Core Complete")

	def imageCore( self, event ):
		self.controller.imageCore(self.coreComplete)