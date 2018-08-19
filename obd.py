#!/usr/bin/env python2

import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 10400)
#ser = serial.Serial('/dev/ttyUSB0', 4800)


blockCounter = 0
ecuString = ""

def init5baud(addr):
	print("Init " + hex(addr) + ": ")
	addr = addr << 1 #Shift for startbit
	addr = addr | 0x100
	for i in range(9):
		val = (addr >> i) & 0x01
		if val == 0:
			print "_",
			ser.break_condition = True
			addr = addr ^ 0x100
		else:
			print "-",
			ser.break_condition = False
		time.sleep(1.0/5.0)
	ser.break_condition = False
	print

def serGetByte():
	v = ser.read(1)
	if len(v) >= 1:
#		print("RX: " + hex(ord(v[0])))
		return ord(v[0])
#	for ch in v:
#		print(hex(ord(ch)))
	return -1

def serSendByte(val):
#	print("TX: " + hex(val))
	ser.write(chr(val))
	#ser.flush()
	ser.read()

def serSendByteACK(val):
	serSendByte(val)
	resp = serGetByte()
	if(resp != (val ^ 0xff)):
		print "BUS ERROR!"
	return resp == (val ^ 0xff)

def serGetByteACK():
	val = serGetByte()
	if val >= 0:
		serSendByte(val ^ 0xff)
	return val

def readingGetString(rType, rVA, rVB):
	if rType == 1:
		return "%d RPM" % (0.2*rVA*rVB)
	if rType == 5:
		return "%d C" % (0.1*rVA*(rVB-100))
	if rType == 7:
		return "%d km/h" % (0.01*rVA*rVB)
	if rType == 17:
		return "\"%c%c\"" % (chr(rVA), chr(rVB))
	if rType == 19:
		return "%d l" % (0.01*rVA*rVB)
	if rType == 36:
		return "%d km" % ((rVA*256+rVB)*10)
	if rType == 37:
		return "Oil Pressure [%d]" % (rVB-30)
	if rType == 64:
		return "%d Ohm" % (rVA+rVB)
	return "UNKNOWN %d: [%d, %d]" % (rType, rVA, rVB)

def recvBlock():
	global blockCounter
#	print("Receiving Block")
	recvLen = 0

	blockLen = serGetByteACK()
	recvLen += 1

	blockCounter = serGetByteACK()
	recvLen += 1

	blockTitle = serGetByteACK()
	recvLen += 1

	data = []
	for i in range(blockLen - recvLen):
		val = serGetByteACK()
		data.append(val)
	
	blockEnd = serGetByte()
	
	if(blockTitle == 0x06):
		print "Type: End Output"
#	if(blockTitle == 0x09):
#		print "Type: ACK"
	if(blockTitle == 0x0A):
		print "Type: NAK"
	if(blockTitle == 0xE7):
#		print "Type: Group Reading"
		for n in range(len(data) / 3):
			readingType = data[n * 3]
			readingValA = data[n * 3 + 1]
			readingValB = data[n * 3 + 2]
#			print("%d: [%d, %d]\t" % (readingType, readingValA, readingValB))
			print("\t%s" % readingGetString(readingType, readingValA, readingValB)),
		print
	if(blockTitle == 0xF6):
		global ecuString
#		print "Type: ASCII"
		asciiStr = ""
		foundZero = False
		lastIdx = 0
		for val in data:
			if(val == 0):
				foundZero = True
				break
			asciiStr = asciiStr + chr(val & 0x7f)
#			print(hex(val) + " " + chr(val))
			lastIdx += 1
#		print(asciiStr)
		ecuString += asciiStr
		if foundZero:
			print(ecuString)
			coding = (data[lastIdx+1] << 8) + data[lastIdx+2]
			print("Coding: %05d" % (coding >> 1))
	if(blockTitle == 0xFC):
#		print "Type: Error list"
		for n in range(len(data) / 3):
			errorCode = (data[n * 3] << 8) + data[n * 3 + 1]
			errorStatus = data[n * 3 + 2]
			errorFlags = errorStatus >> 6
			if(errorFlags > 1):
				errorFlags += 8
			if(errorCode < 0xffff):
				print(" - %05d: {%02d-%02d}" % (errorCode, errorStatus&0x3F, errorFlags))
	return blockTitle
	
def sendBlock(blockTitle, blockContent = []):
	global blockCounter
	blockCounter = (blockCounter + 1) & 0xff
	serSendByteACK(0x03 + len(blockContent))
	serSendByteACK(blockCounter)
	serSendByteACK(blockTitle)
	for item in blockContent:
		serSendByteACK(item)
	serSendByte(0x03)

def sendBlockAck():
	sendBlock(0x09)

def sendBlockEnd():
	sendBlock(0x06)

def getErrorCodes():
	print("Error Codes:")
	sendBlock(0x07)
	while True:
		bT = recvBlock()
		if bT != 0xFC:
			break
		sendBlockAck()

lastGrp = -1

def readGroup(grp):
	global lastGrp
	if grp != lastGrp:
		print("Reading Group %d" % grp)
		lastGrp = grp
	sendBlock(0x29, [grp])
	bt = recvBlock()
#	print(hex(bt))
#	sendBlockAck()

def initDevice():
	syncVal = serGetByte() #55
	if(syncVal != 0x55):
		print("syncVal: %x" % syncVal)
		return
	serGetByte() #01
	serGetByte() #8A
	serSendByte(0x75)
	while True:
		bT = recvBlock()
		if bT == 0x09:
			break
		sendBlockAck()

	getErrorCodes()
#	readGroup(0)
#	readGroup(1)
#	readGroup(2)
#	readGroup(3)
#	readGroup(4)
#	readGroup(5)
	lT = time.time()
#	while True:
#		readGroup(2)
#		ct = time.time()
#		print ct-lT
#		lT = ct
#	for i in range(256):
#		readGroup(i)
	sendBlockEnd()
		

init5baud(0x17)
ser.timeout = 0
ser.read(100)
ser.timeout = 1
initDevice()

ser.close()

