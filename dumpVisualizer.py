#!/usr/bin/env python3

f = open("/tmp/uart_00141", "rb")
inV = f.read(1)

running = False
i = 0
ecu = True
count = -1

while (len(inV) > 0):
	val = inV[0]
	Sval = val
	if Sval < 0x21:
		Sval = 0x20

	if Sval > 0x7E:
		Sval = 0x20
#	print(val)
	if(running):
		if count < 0:
			count = val 
			ecu = not ecu
		if ecu:
			print("%02x" % val)
		else:
			print("\t%02x %c" % (val, chr(Sval)))
		count -= 1
		if count >= 0:
			f.read(1)
		

	if((running == False) & (val == 0x75)):
		running = True
		i = 0
	i += 1
	inV = f.read(1)
