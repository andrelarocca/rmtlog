import socket
import struct

def carry_around_add(a, b):
	c = a + b
	return(c &0xffff)+(c >>16)

# Internet checksum algorithm
def checksum(msg):
	if len(msg) & 1:  # Correct for odd number of bytes
		msg += "\x00"
	s = 0
	for i in range(0, len(msg),2):
		w = ord(msg[i])+(ord(msg[i+1])<<8)
		s = carry_around_add(s, w)
	return~s &0xffff

# Create frame by reading from the input file. If flag is_ack == True, create ACK for that frame_id.
# Returns the a tuple: (frame, is_last).
def create_frame(input_file, max_payload_length, frame_id, is_ack):
	SYNC = "\xDC\xC0\x23\xC2"
	payload = ""
	payload_length = 0
	is_last = False
	flags = 128  # ACK flag

	if not is_ack:
		payload = input_file.read(max_payload_length)
		payload_length = len(payload)
		is_last = True if (payload_length < max_payload_length) else False
		flags = 64 if is_last else 0  # Set END flag if last frame

	print "Creating frame"
	if is_ack: print "ACK FRAME [id = %d]\n" %frame_id
	else: print "DATA FRAME [id = %d][length = %d]\n" %(frame_id, payload_length)

	payload_length = struct.pack("!H", payload_length)  # Has two bytes so needs to set byte order
	frame_id = struct.pack("B", frame_id)
	flags = struct.pack("B", flags)

	# Frame with filler for chksum
	frame = SYNC + SYNC + "\x00\x00" + payload_length + \
			frame_id + flags + payload

	chksum = struct.pack("!H", checksum(frame))  # Calculate and pack checksum value for ready-to-send frame

	# Frame with chksum in big-endian(needs to unpack to little-endian so checksum results in 0)
	frame = SYNC + SYNC + chksum + payload_length + \
			frame_id + flags + payload

	return frame, is_last

# Send frame through the network. Exists only as a way to standardize code.
def send_frame(dcc_socket, frame):
	print "Sending frame\n"
	dcc_socket.sendall(frame)

# Checks double SYNC in header 
def receive_sync(dcc_socket):
	double_sync = "\xDC\xC0\x23\xC2\xDC\xC0\x23\xC2"  # SYNC + SYNC
	state  = 0

	# State machine that checks each byte of the SYNC
	while state < 8:
		data = dcc_socket.recv(1)
		if data:
			if data == double_sync[state]:
				state += 1;
			else:
				return False
	
	return True

# Checks the validity of the header. If something goes wrong along the checking it returns a tuple of Nones.
# Returns a tuple: (payload, chksum, frame_id, is_last, is_ack).
def receive_frame(dcc_socket):
	SYNC = "\xDC\xC0\x23\xC2"

	print "Receiving frame"

	if(receive_sync(dcc_socket)):  # Goes ahead if double SYNC was checked
		# Receive header fields and unpack them accordingly
		chksum = struct.unpack("!H", dcc_socket.recv(2))[0]
		length = struct.unpack("!H", dcc_socket.recv(2))[0]
		frame_id = struct.unpack("B", dcc_socket.recv(1))[0]
		flags = struct.unpack("B", dcc_socket.recv(1))[0]

		# Set the frame in order to process checksum
		frame = SYNC + SYNC + struct.pack("H", chksum) + struct.pack("!H", length) + \
				struct.pack("B", frame_id) + struct.pack("B", flags)

		if length == 0 and flags == 128:  # is ACK
			# ACK was not disrupted
			if not checksum(frame):  # Valid ACK
				print "ACK FRAME [id = %d]\n" %frame_id
				return None, chksum, frame_id, False, True
			else:
				print "ACK checksum fail\n"
				return None, None, None, None, None

		payload = dcc_socket.recv(length)
		frame += payload

		if flags == 0 or flags == 64:		
			is_last = True if (flags == 64) else False  # flag 64 stands for last data frame

			if not checksum(frame):  # Valid Data Frame
				print "DATA FRAME [id = %d][length = %d]\n" %(frame_id, length)
				return payload, chksum, frame_id, is_last, False
			else:
				print "Data frame checksum fail\n"
				return None, None, None, None, None	

	print "Invalid header"
	return None, None, None, None, None

# Saves payload from received frame to the output file. Exists only as a way to standardize code.
def save_payload(output_file, payload):
	output_file.write(payload)