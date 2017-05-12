import socket
import struct

def carry_around_add(a, b):
	c = a + b
	return(c &0xffff)+(c >>16)

def checksum(msg):
	if len(msg) & 1:
		msg += "\x00"
	s = 0
	for i in range(0, len(msg),2):
		w = ord(msg[i])+(ord(msg[i+1])<<8)
		s = carry_around_add(s, w)
	return~s &0xffff

def create_frame(input_file, max_payload_length, frame_id, is_ack):
#	print "Creating frame", frame_id, ". Is it ack?", is_ack

	SYNC = "\xDC\xC0\x23\xC2"
	payload = ""
	payload_length = 0
	is_last = False
	flags = 128  # ACK flag

	if not is_ack:
		payload = input_file.read(max_payload_length)
		payload_length = len(payload)
		is_last = True if (payload_length < max_payload_length) else False
		flags = 64 if is_last else 0 

	payload_length = struct.pack("H", payload_length)
	frame_id = struct.pack("B", frame_id)
	flags = struct.pack("B", flags)

	frame = SYNC + SYNC + "\x00\x00" + payload_length + \
			frame_id + flags + payload

#	print "Created frame without checksum:" ,
#	for i in frame:
#		print ord(i),
#	print "Checksum:", checksum(frame)

	chksum = struct.pack("!H", checksum(frame))
	payload_length = struct.pack("!H", struct.unpack("H", payload_length)[0])

	frame = SYNC + SYNC + chksum + payload_length + \
			frame_id + flags + payload

#	print "Created frame with checksum:   " ,
#	for i in frame:
#		print ord(i),
#	print

	return frame, is_last

# Send frame through the network. Exists only as a way to standardize code.
def send_frame(dcc_socket, frame):
	dcc_socket.sendall(frame)

# State machine 
def receive_sync(dcc_socket):
	double_sync = "\xDC\xC0\x23\xC2\xDC\xC0\x23\xC2"  # SYNC + SYNC
	state  = 0

	while state < 8:
		data = dcc_socket.recv(1)
		if data:
			if data == double_sync[state]:
				state += 1;
			else:
				return False
	
	return True

# Checks the validity of the header. If something goes wrong along the checking it returns a tuple of Nones
# Returns a tuple: (payload, chksum, frame_id, is_last, is_ack).
def receive_frame(dcc_socket):
	SYNC = "\xDC\xC0\x23\xC2"

	print "Receiving frame"

	if(receive_sync(dcc_socket)):
		chksum = struct.unpack("!H", dcc_socket.recv(2))[0]
#		print "chksum:", chksum
		length = struct.unpack("!H", dcc_socket.recv(2))[0]
#		print "length:", length
		frame_id = struct.unpack("B", dcc_socket.recv(1))[0]
#		print "frame_id:", frame_id
		flags = struct.unpack("B", dcc_socket.recv(1))[0]
#		print "flags:", flags

		frame = SYNC + SYNC + struct.pack("H", chksum) + struct.pack("H", length) + \
				struct.pack("B", frame_id) + struct.pack("B", flags)

		if length == 0 and flags == 128:  # is ACK
			# ACK was not disrupted
			if not checksum(frame):
				print "ACK FRAME [id = %d]" %frame_id
				return None, chksum, frame_id, False, True
			else:
				return None, None, None, None, None

		payload = dcc_socket.recv(length)
		frame += payload
		is_last = True if (flags == 64) else False

#		print "Data frame:" ,
#		for i in frame:
#			print ord(i),

#		print "Checksum:", checksum(frame)
		if not checksum(frame): # Valid Frame
			print "DATA FRAME [id = %d][length = %d]" %(frame_id, length)
			return payload, chksum, frame_id, is_last, False

	print "Frame invalid"
	return None, None, None, None, None

# Saves payload from received frame to the output file. Exists only as a way to standardize code.
def save_payload(output_file, payload):
	output_file.write(payload)