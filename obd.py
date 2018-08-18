#!/usr/bin/env python2

import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 10400)
ser.timeout = 0
ser.read(100)


blockCounter = 0

def init5baud(addr):
	print("Init " + hex(addr) + ": ")
#	addr = addr << 1
#	addr += 0x01
	addr += 0x100
	for i in range(8):
		val = (addr << i) & 0x100
		if val > 0:
			print "_",
		else:
			print "-",
		ser.break_condition = val > 0
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
	ser.flush()
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
	return "UNKNOWN %d: [%d, %d]" % rType, rVA, rVB

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
	if(blockTitle == 0x09):
		print "Type: ACK"
	if(blockTitle == 0x0A):
		print "Type: NAK"
	if(blockTitle == 0xE7):
		print "Type: Group Reading"
		for n in range(len(data) / 3):
			readingType = data[n * 3]
			readingValA = data[n * 3 + 1]
			readingValB = data[n * 3 + 2]
i#			print("%d: [%d, %d]\t" % (readingType, readingValA, readingValB))
			print(readingGetString(readingType, readingValA, readingValB))
	if(blockTitle == 0xF6):
		print "Type: ASCII"
		asciiStr = ""
		for val in data:
			asciiStr = asciiStr + chr(val & 0x7f)
#			print(hex(val) + " " + chr(val))
		print(asciiStr)
	if(blockTitle == 0xFC):
		print "Type: Error list"
		for n in range(len(data) / 3):
			errorCode = (data[n * 3] << 8) + data[n * 3 + 1]
			errorStatus = data[n * 3 + 2]
			if(errorCode < 0xffff):
				print(" - {}: {}".format(errorCode, errorStatus))
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
	sendBlock(0x07)
	while True:
		bT = recvBlock()
		if bT != 0xFC:
			break
		sendBlockAck()

def readGroup(grp):
	print("Reading Group %d" % grp)
	sendBlock(0x29, [grp])
	bt = recvBlock()
#	print(hex(bt))
#	sendBlockAck()

def initDevice():
	serGetByte() #55
	serGetByte() #01
	serGetByte() #8A
	serSendByte(0x75)
	while True:
		bT = recvBlock()
		if bT == 0x09:
			break
		sendBlockAck()

	getErrorCodes()
	readGroup(0)
	readGroup(1)
	readGroup(2)
	readGroup(3)
	readGroup(4)
	readGroup(5)
	sendBlockEnd()
		

init5baud(0x17)

ser.timeout = 0
ser.read(100)
ser.timeout = 1

initDevice()

ser.close()

