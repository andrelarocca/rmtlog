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

data = "dc c0 23 c2 dc c0 23 c2 00 00 00 04 00 00 01 02 03 04"

data = data.split()
data = map(lambda x: int(x,16), data)
data = struct.pack("%dB" % len(data), *data)

print ' '.join('%02X' % ord(x) for x in data)

(a,) = struct.unpack("H", struct.pack(">H", checksum(data)))
print "Checksum: 0x%04x" % checksum(data), "Packed: 0x%04x" % a 