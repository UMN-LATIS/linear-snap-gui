from math import floor
import os
import sys
import threading
import serial;
import time
from pubsub import pub

class miniMacroControl:

	callback = None;
	halt = False;
	coreId = "Unknown Core"
	railPosition = {"S": 0, "L": 0}
	photoCount = 0
	positionCount = 0
	arduino = None

	def __init__(self, config):
		self.config = config
		try:
			self.arduino = serial.Serial(port='/dev/cu.usbmodem11201',
								baudrate=115200, timeout=.1)
		except:
			print("No Arduino Found")
			
		pub.subscribe(self.endOfCore, "coreStatus")


	def runRail(self, rail, direction):
		self.railPosition[rail] = sys.maxsize
		print(self.write_read("R" + " " + str(rail) + " " + str(direction) + " 600"))

	def moveRail(self, rail, direction, distance):
		self.railPosition[rail] = self.railPosition[rail] + (int(distance) * (1 if direction == 1 else -1))
		data = self.write_read("M" + " " + rail + " " + str(direction) + " " + str(distance) + " 2200")
		while(data != "POSITIONED\r\n"):
			data = self.readData()
			if(self.halt):
				return
			time.sleep(0.1)
		return


	def stopRail(self, rail):
		print(self.write_read("S" + " " + rail))

	def goHome(self):
		data = self.write_read("H");
		while(data != "HOME\r\n"):
			data = self.readData()
			if(self.halt):
				return
			time.sleep(0.1)

	def write_read(self, x):
		if(self.arduino is not None):
			self.arduino.reset_input_buffer()
			self.arduino.write(bytes(x + "\n", 'ASCII'))
			time.sleep(0.05)
			data = self.arduino.readline().decode('ASCII')
			print(data);
			return data

	def readData(self):
		if(self.arduino is not None):
			data = self.arduino.readline().decode('ASCII')
			print(data)
			return data

	def findFocus(self, camera=None):
		# find focus
		if(camera):
			self.camera = camera
		self.camera.setLiveView(True)
		time.sleep(2)
		previousFocusValue = 0
		focalValues = []
		previousFocusAverage = 0
		print("Moving to start position")
		self.moveRail("L",1, 500 );
		
		print("Moved")
		while(True):
			if(len(focalValues) < 6):
				focalValues.append(self.camera.laplacian)
				time.sleep(0.08)
				continue;

			cameraAverage = sum(focalValues) / len(focalValues)
			print("Average: ", cameraAverage, " Previous: ", previousFocusAverage)
			if(round(cameraAverage) - round(previousFocusAverage) < -1):
				print("Focus found, average is ", cameraAverage)
				break
			if(self.halt):
				return
			previousFocusAverage = max(cameraAverage, previousFocusAverage)
			focalValues = []
			self.moveRail("S", 1, 2);

		print("Moving to start position")
		self.moveRail("L",0, 500 );
		
		self.camera.setLiveView(False)
		self.focalPosition = self.railPosition["S"]
		print("Focal Position: ", self.focalPosition)
		time.sleep(4)

	def endOfCore(self, message):
		self.halt = True
		time.sleep(0.1)
		self.goHome()

	def imageCore(self, coreId, callback, camera):
		self.coreId = coreId
		self.halt = False
		self.camera = camera
		print("Starting ", self.coreId)

		self.callback = callback;
		if(self.halt):
			return;

		print("Seeking Home")
		self.goHome();
		
		time.sleep(1)
		#assuming we made it home, we reset our position indicators
		self.railPosition["S"] = 0;
		self.railPosition["L"] = 0;

		# move to approximate focus position
		print("going to focal plane")
		self.moveRail("S", 1, self.config.configValues["StartPosition"]);
		
		self.findFocus()		
		# start camera logging
		t = threading.Thread(target=self.camera.waitForPhoto,
								args=(self.coreId,), name='camera-worker')
		t.daemon = True
		t.start()
		time.sleep(2)
		print("Moving to start position")
		self.moveRail("S",1, 10 );
		
		time.sleep(1)
		self.positionCount = 0;
		while(1):
			print("Starting Position")
			if(self.halt):
				return

			print("Starting capture for position ", self.positionCount)
			for i in range(0,int(self.config.configValues["StackDepth"])):
				print("Position ", i)
				self.write_read("P");
				time.sleep(0.2)
				self.moveRail("S", 0, 1);
				time.sleep(0.1)
				if(self.halt):
					return
			if(self.halt):
				return
			
			print("Moving to next position")
			# could refactor this so that the rails move at the same time
			self.moveRail("S", 1, int(self.config.configValues["StackDepth"]))
			self.moveRail("L", 1, int(self.config.configValues["Overlap"]))

			time.sleep(1)
			self.positionCount = self.positionCount + 1
		self.callback()
