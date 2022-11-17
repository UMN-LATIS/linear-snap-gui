import serial;
import time

class miniMacroControl:
	arduino = serial.Serial(port='/dev/cu.usbmodem101',
	                        baudrate=9600, timeout=.1)
	callback = None;
	halt = False;
	coreId = "Unknown Core"

	def runRail(self, rail, direction):
		print(self.write_read("R" + " " + rail + " " + direction + " 600"))

	def moveRail(self, rail, direction, distance):
		return self.write_read("M" + " " + rail + " " + direction + " " + distance + " 1000")

	def stopRail(self, rail):
		print(self.write_read("S" + " " + rail))

	def goHome(self):
		self.write_read("H")

	def findFocus(self):
		print(self.write_read("F"))

	def write_read(self, x):
		self.arduino.reset_input_buffer()
		self.arduino.write(bytes(x + "\n", 'ASCII'))
		time.sleep(0.05)
		data = self.arduino.readline()
		return data

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
		
		while(1):
			print("Starting Position")
			surfaceValues = [];	
			if(self.halt):
				return
			print("Finding Focus")
			data = self.findFocus();
			print(data)
			while("FOCUS" not in data):
				data = self.arduino.readline()
				if(self.halt):
					return
				time.sleep(0.1)
				print(data)

			coreSurface = data.split(":")[1]
			surfaceValues.append(coreSurface)
			if(abs(surfaceValues.mean() - coreSurface) > surfaceValues.stddev()):
				print("Core somewhere weird or end of core found")
				return;
			
			if(self.halt):
				return
			print("Moving to start position")
			data = self.moveRail("S",0, "30" );
			print(data)
			while(data != "POSITIONED\r\n"):
				data = self.arduino.readline()
				if(self.halt):
					return
				time.sleep(0.1)
				print(data)
			print("Starting capture")
			for i in range(1, 8):
				print("Position ", i)
				self.write_read("P");
				data = self.moveRail("S", 1, 10);
				print(data)
				while(data != "POSITIONED\r\n"):
					data = self.arduino.readline()
					if(self.halt):
						return
					time.sleep(0.1)
					print(data)

			print("Moving to next position")
			data = self.moveRail("S", 0, 50)
			data = self.moveRail("L", 1, 50)
			print(data)
			while(data != "POSITIONED\r\n"):
				data = self.arduino.readline()
				if(self.halt):
					return
				time.sleep(0.1)
				print(data)
		self.callback()
