def carry_around_add(a, b):
    c = a + b
    return(c &0xffff)+(c >>16)

def checksum(msg):
    s =0
    for i in range(0, len(msg),2):
        w = ord(msg[i])+(ord(msg[i+1])<<8)
        s = carry_around_add(s, w)
    return~s &0xffff

import struct

data = "dc c0 23 c2 dc c0 23 c2 00 00 00 04 00 00 01 02 03 04 05 06"

data = data.split()
data = map(lambda x: int(x,16), data)
data = struct.pack("%dB" % len(data), *data)

print ' '.join('%02X' % ord(x) for x in data)

(a,) = struct.unpack("H", struct.pack(">H", checksum(data)))
print "Checksum: 0x%04x" % checksum(data), "Packed: 0x%04x" % a 

checksum_data = struct.pack("!H", checksum(data))

print "Checksum data:",
for i in checksum_data:
	print ord(i),
print


frame = "\xDC\xC0\x23\xC2\xDC\xC0\x23\xC2\x00\x00\x00\x04\x00\x00\x01\x02\x03\x04\x05\x06"

print "Previous frame:", frame, "Checksum:", checksum(frame)

print "ord(Frame):",
for i in frame:
	print ord(i),

print 

frame = "\xDC\xC0\x23\xC2\xDC\xC0\x23\xC2" + struct.pack("H", checksum(data)) + "\x00\x04\x00\x00\x01\x02\x03\x04\x05\x06"

print "New frame:", frame, "Checksum:", checksum(frame)

print "ord(Frame):",
for i in frame:
	print ord(i),
