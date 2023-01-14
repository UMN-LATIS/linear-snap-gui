import os
import sys
import serial;
import time

class miniMacroControl:

	callback = None;
	halt = False;
	coreId = "Unknown Core"
	railPosition = {"S": 0, "L": 0}
	photoCount = 0
	positionCount = 0


	def __init__(self):
		try:
			self.arduino = serial.Serial(port='/dev/cu.usbmodem11201',
								baudrate=9600, timeout=.1)
		except:
			print("No Arduino Found")
			

	def halt(self):
		self.halt = True

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
		self.arduino.reset_input_buffer()
		self.arduino.write(bytes(x + "\n", 'ASCII'))
		time.sleep(0.05)
		data = self.arduino.readline().decode('ASCII')
		return data

	def readData(self):
		data = self.arduino.readline().decode('ASCII')
		return data

	def findFocus(self):
		print("Hey")

	def imageCore(self, coreId, callback):
		self.coreId = coreId
		print("Starting ", self.coreId)

		self.callback = callback;
		if(self.halt):
			return;

		print("Seeking Home")
		data = self.goHome();
		print(data)
		while(data != "HOME\r\n"):
			data = self.arduino.readline()
			if(self.halt):
				return
			time.sleep(0.1)
			print(data)

		#assuming we made it home, we reset our position indicators
		self.railPosition["S"] = 0;
		self.railPosition["L"] = 0;

		self.positionCount = 0;
		while(1):
			print("Starting Position")
			surfaceValues = [];	
			if(self.halt):
				return
			print("Finding Focus")
			# data = self.findFocus();
			# print(data)
			# while("FOCUS" not in data):
			# 	data = self.arduino.readline()
			# 	if(self.halt):
			# 		return
			# 	time.sleep(0.1)
			# 	print(data)

			# coreSurface = data.split(":")[1]
			# surfaceValues.append(coreSurface)
			# if(abs(surfaceValues.mean() - coreSurface) > surfaceValues.stddev()):
			# 	print("Core somewhere weird or end of core found")
			# 	return;
			
			# if(self.halt):
			# 	return
			# print("Moving to start position")
			# data = self.moveRail("S",0, "30" );
			# print(data)
			# while(data != "POSITIONED\r\n"):
			# 	data = self.arduino.readline()
			# 	if(self.halt):
			# 		return
			# 	time.sleep(0.1)
			# 	print(data)
			print("Starting capture")
			for i in range(1, 21):
				print("Position ", i)
				self.write_read("P");
				time.sleep(0.3)
				data = self.moveRail("S", 0, 1);
				print(data)
				while(data != "POSITIONED\r\n"):
					data = self.readData()
					if(self.halt):
						return
					print(data)
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
				print(data)
			self.positionCount = self.positionCount + 1
			if(self.positionCount == 10):
				return;
		self.callback()
