from math import floor
import os
import sys
import threading
import serial;
import time
from pubsub import pub

class LinearSnapControl:

	callback = None;
	halt = False;
	coreId = "Unknown Core"
	railPosition = {"S": 0, "L": 0}
	photoCount = 0
	positionCount = 0
	arduino = None
	coreSize = "Small"

	def __init__(self, config):
		self.config = config
		try:
			self.arduino = serial.Serial(port=self.config.configValues["SerialPort"],
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

	def toggleLight(self, light):
		if(light):
			self.write_read("L1")
		else:
			self.write_read("L0")

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

	def findInitialFocus(self, camera=None):
		
		print("Moving to start position")
		self.moveRail("L",1, 500 );
		
		print("Moved")
		self.findFocus(camera)

		print("Moving to start position")
		self.moveRail("L",0, 500 );

	def findFocus(self, camera=None):
		# find focus
		if(camera):
			self.camera = camera
		self.camera.setLiveView(True)
		
		# move to approximate focus position
		print("going to focal plane")

		if(self.coreSize == "Tall"): 
			self.moveRail("S", 1, self.config.configValues["StartPositionBig"]);
		else:
			self.moveRail("S", 1, self.config.configValues["StartPositionSmall"]);

		
		time.sleep(2)
		previousFocusValue = 0
		focalValues = []
		previousFocusAverage = 0
		focusFound = False
		while(True):
			if(len(focalValues) < 6):
				focalValues.append(self.camera.laplacian)
				time.sleep(0.08)
				continue;

			if(self.camera.likelyBlank):
				print("Blank image, stopping")
				break

			cameraAverage = sum(focalValues) / len(focalValues)
			print("Average: ", cameraAverage, " Previous: ", previousFocusAverage)
			if(round(cameraAverage) - round(previousFocusAverage) < -1):
				focusFound = True
				print("Focus found, average is ", cameraAverage)
				break
			if(self.halt):
				self.camera.setLiveView(False)
				return
			previousFocusAverage = max(cameraAverage, previousFocusAverage)
			focalValues = []
			self.moveRail("S", 1, 2);
		self.camera.setLiveView(False)
		if(focusFound):
			#back out one step since we're too far in by the time we find focus
			self.moveRail("S", 0, 2);
			self.focalPosition = self.railPosition["S"]
			print("Focal Position: ", self.focalPosition)
		time.sleep(4)
		
	def triggerHalt(self):
		self.halt = True
		self.toggleLight(False)
		while(self.arduino.in_waiting):
			t = self.arduino.read()

	def endOfCore(self, message):
		self.halt = True
		time.sleep(0.1)
		self.toggleLight(False)
		# self.goHome()

	def imageCore(self, coreId, callback, camera, coreSize):
		self.toggleLight(True)
		self.positionCount = 0
		self.photoCount = 0
		self.railPosition = {"S": 0, "L": 0}
		
		self.coreId = coreId
		self.halt = False
		self.camera = camera
		self.camera.reset()
		self.coreSize = coreSize
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


		self.findInitialFocus()

		if(self.halt):
			return
		
		self.camera.prepForCore(self.coreId)
		# start camera logging
		t = threading.Thread(target=self.camera.waitForPhoto,
								args=(self.coreId,), name='camera-worker')
		t.daemon = True
		t.start()
		time.sleep(2)
		print("Moving to start position")
		self.moveRail("S",1, round(int(self.config.configValues["StackDepth"]) / 2) );
		
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
			
			if(self.positionCount % int(self.config.configValues["Refocus"]) == 0 or self.camera.requiresRefocus):
				print("Refocusing")
				self.camera.stopWaiting = True
				time.sleep(3)
				self.moveRail("S", 0, self.railPosition["S"])
				self.findFocus()
				self.moveRail("S",1, round(int(self.config.configValues["StackDepth"]) / 2) )
				self.camera.requiresRefocus = False
				t = threading.Thread(target=self.camera.waitForPhoto,
					args=(self.coreId,), name='camera-worker')
				t.daemon = True
				t.start()
				if(self.halt):
					return
		
		self.callback()
