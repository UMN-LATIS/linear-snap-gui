import serial;


class miniMacroControl:
	arduino = serial.Serial(port='/dev/cu.Bluetooth-Incoming-Port', baudrate=115200, timeout=.1)
	callback = None;
	halt = False;

	def runRail(self, rail, direction):
		self.write_read("R" + " " + rail + " " + direction + " 600")

	def moveRail(self, rail, direction, distance):
		return self.write_read("M" + " " + rail + " " + direction + " " + distance + " 1000")

	def stopRail(self, rail):
		self.write_read("S" + " " + rail)

	def goHome(self):
		self.write_read("H")

	def findFocus(self):
		self.write_read("F")

	def write_read(self, x):
		self.arduino.write(bytes(x, 'utf-8'))
		time.sleep(0.05)
		data = self.arduino.readline()
		return data

	def imageCore(self, callback):
		self.callback = callback;
		if(self.halt):
			return;
		data = self.goHome();
		print(data)
		while(data != "HOME\r\n"):
			data = self.arduino.readline()
			if(self.halt):
				return
			time.sleep(0.1)
			print(data)
		
		while(1):
			surfaceValues = [];	
			if(self.halt):
				return
			
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
			data = self.moveRail("S",0, "30" );
			print(data)
			while(data != "POSITIONED\r\n"):
				data = self.arduino.readline()
				if(self.halt):
					return
				time.sleep(0.1)
				print(data)
		
			for i in range(1, 8):
				self.write_read("P");
				data = self.moveRail("S", 1, 10);
				print(data)
				while(data != "POSITIONED\r\n"):
					data = self.arduino.readline()
					if(self.halt):
						return
					time.sleep(0.1)
					print(data)

			data = self.moveRail("S", 0, 50)
			data = self.moveRail("L", 1, 50)
			print(data)
			while(data != "POSITIONED\r\n"):
				data = self.arduino.readline()
				if(self.halt):
					return
				time.sleep(0.1)
				print(data)

