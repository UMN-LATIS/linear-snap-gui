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

	def __init__(self):
		try:
			self.arduino = serial.Serial(port='/dev/cu.usbmodem11201',
								baudrate=9600, timeout=.1)
		except:
			print("No Arduino Found")
			
		pub.subscribe(self.endOfCore, "coreStatus")


	def runRail(self, rail, direction):
		self.railPosition[rail] = sys.maxint
		print(self.write_read("R" + " " + rail + " " + direction + " 600"))

	def moveRail(self, rail, direction, distance):
		self.railPosition[rail] = self.railPosition[rail] + (distance * (1 if direction == 1 else -1))
		return self.write_read("M" + " " + rail + " " + str(direction) + " " + str(distance) + " 1000")

	def stopRail(self, rail):
		print(self.write_read("S" + " " + rail))

	def goHome(self):
		self.write_read("H")

	def write_read(self, x):
		if(self.arduino is not None):
			self.arduino.reset_input_buffer()
			self.arduino.write(bytes(x + "\n", 'ASCII'))
			time.sleep(0.05)
			data = self.arduino.readline().decode('ASCII')
			return data

	def readData(self):
		if(self.arduino is not None):
			data = self.arduino.readline().decode('ASCII')
			return data

	def findFocus(self, camera=None):
		# find focus
		if(camera):
			self.camera = camera
		self.camera.setLiveView(True)
		previousFocusValue = 0
		focalValues = []
		previousFocusAverage = 0
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
			
			previousFocusAverage = max(cameraAverage, previousFocusAverage)
			focalValues = []
			self.moveRail("S", 1, 1);

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
		data = self.goHome();
		while(data != "HOME\r\n"):
			data = self.readData()
			if(self.halt):
				return
			time.sleep(0.1)

		#assuming we made it home, we reset our position indicators
		self.railPosition["S"] = 0;
		self.railPosition["L"] = 0;

		# move to approximate focus position
		print("going to focal plane")
		data = self.moveRail("S", 0, 30);
		print(data)
		while(data != "POSITIONED\r\n"):
			data = self.readData()
			if(self.halt):
				return
			time.sleep(0.1)


		self.findFocus()		
		# start camera logging
		t = threading.Thread(target=self.camera.waitForPhoto,
								args=(self.coreId,), name='camera-worker')
		t.daemon = True
		t.start()

		print("Moving to start position")
		data = self.moveRail("S",1, 10 );
		while(data != "POSITIONED\r\n"):
			data = self.arduino.readline()
			if(self.halt):
				return
			time.sleep(0.1)
		self.positionCount = 0;
		while(1):
			print("Starting Position")
			if(self.halt):
				return

			print("Starting capture for position ", self.positionCount)
			for i in range(1, 21):
				print("Position ", i)
				self.write_read("P");
				time.sleep(0.3)
				data = self.moveRail("S", 0, 1);
				while(data != "POSITIONED\r\n"):
					data = self.readData()
					if(self.halt):
						return
					time.sleep(0.1)
				if(self.halt):
					return
			if(self.halt):
				return
			
			print("Moving to next position")
			data = self.moveRail("S", 1, 20)
			data = self.moveRail("L", 0, 150)

			while(data != "POSITIONED\r\n"):
				data = self.readData()
				if(self.halt):
					return
				time.sleep(0.1)
			self.positionCount = self.positionCount + 1
			if(self.positionCount == 10):
				return;
		self.callback()
