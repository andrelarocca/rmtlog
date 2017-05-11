import sys
import struct

f = open(sys.argv[1], "rb")
#output_file = open(sys.argv[2], "wb")


frame = "\xDC\xC0\x23\xC2"
byte = f.read(1)
while byte:
	frame += byte
	byte = f.read(1)	

print frame

"""

while True:
	buf = input_file.read(16)
	if not buf: break;
	print "Buf: ", buf
	le = len(buf)
	#buf = bytes(buf)
	buf = struct.pack(">I", len(buf)) + buf
	print "Packed:", buf
	(i,), data = struct.unpack(">I", buf[:4]), buf[4:]
	data = data[:i]
	print "i:", i, "Data:", data

	
	frame = "\xDC\xC0\x23\xC2"
	print "Frame:", frame
	frame += struct.pack(">I", int(data, 16))
	print "Frame + Data:", frame

	a, b = teste()
	print a

	#a = 128
	#a = struct.pack("I", a)
	#print a
	#print a == 128
	#(a,) = struct.unpack("I", a)
	#print a

while True:
	buf = input_file.read(16)
	if not buf: break;
	#buf = str(buf)
	print "Buf: ", buf
	le = len(buf)
	#buf = bytes(buf)
	buf = struct.pack(">I", len(buf)) + buf
	(i,), data = struct.unpack(">I", buf[:4]), buf[4:]
	data = data[:i]
	print "i:", i, "Data:", data

	
	frame = "\xDC\xC0\x23\xC2"
	print "Frame:", frame
	frame += struct.pack(">I", int(data, 16))
	print "Frame + Data:", frame

	#a = 128
	#a = struct.pack("I", a)
	#print a
	#print a == 128
	#(a,) = struct.unpack("I", a)
	#print a




while True:
	buf = input_file.read(16)
	if not buf: break;
	buf = int(buf,16)
	print "Buf: ", buf
	buf = struct.pack(">B", buf)
	buf = struct.unpack(">B", buf)
	print "Buf unpacked", buf
"""