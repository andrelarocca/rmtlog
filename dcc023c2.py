#!/usr/bin/env python

###########################################
#               Redes - TP1               #
#                                         # 
# Autores: Joao Francisco B. S. Martins   #
#          Vitor Bernardo Rodrigues Jorge #                 
#                                         # 
# Matriculas: 2013007498                  #
#             2013007803                  #
###########################################

""" TODO
 - Separar em main e lib dccnet
 - Talvez tenhamos que fazer loop para receber em receive_frame
 - Detectar fechamento de socket
"""

""" DUVIDAS
 - Socket passivo tem que morrer ou continua esperando novas conexoes? SIM
 - Checar se socket.rcv(0) buga - NAO BUGA, retorna ""
"""

import sys
import socket
import struct
import time

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
	print "Creating frame", frame_id, ". Is it ack?", is_ack

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

	payload_length = struct.pack(">H", payload_length)
	frame_id = struct.pack(">B", frame_id)
	flags = struct.pack(">B", flags)

	frame = SYNC + SYNC + "\x00\x00" + payload_length + \
			frame_id + flags + payload

	print "Created frame without checksum:" ,
	for i in frame:
		print ord(i),

	print "Checksum:", checksum(frame)

	chksum = struct.pack(">H", checksum(frame))

	frame = SYNC + SYNC + chksum + payload_length + \
			frame_id + flags + payload

	print "Created frame with checksum:   " ,
	for i in frame:
		print ord(i),
	print

	return frame, is_last

# Send frame through the network. Exists only as a way to standardize code.
def send_frame(dcc_socket, frame):
	dcc_socket.sendall(frame)

def receive_header(dcc_socket):
	header = "\xDC\xC0\x23\xC2\xDC\xC0\x23\xC2"
	state  = 0

	while state < 8:
		data = dcc_socket.recv(1)
		if data:
			if data == header[state]:
				state += 1;
			else:
				return False
	
	return True

# Automata that checks the validity of the header. If nothing is received or one of the states fails, it returns
# Returns frame payload.
def receive_frame(dcc_socket):
	SYNC = "\xDC\xC0\x23\xC2"

	print
	print "Receiving frame"

	if(receive_header(dcc_socket)):
		(chksum,) = struct.unpack(">H", dcc_socket.recv(2))
		print "chksum:", chksum
		(length,) = struct.unpack(">H", dcc_socket.recv(2))
		print "length:", length
		(frame_id,) = struct.unpack(">B", dcc_socket.recv(1))
		print "frame_id:", frame_id
		(flags,) = struct.unpack(">B", dcc_socket.recv(1))
		print "flags:", flags

		frame = SYNC + SYNC + struct.pack("H", chksum) + struct.pack(">H", length) + \
				struct.pack(">B", frame_id) + struct.pack(">B", flags)

		if length == 0 and flags == 128: # ACK
			return None, None, frame_id, False, True

		payload = dcc_socket.recv(length)
		frame += payload
		is_last = True if (flags == 64) else False

		print "Received frame:" ,
		for i in frame:
			print ord(i),

		print "Checksum:", checksum(frame)
		if not checksum(frame): # Valid Frame
			print "Frame is valid"
			return payload, chksum, frame_id, is_last, False

	return None, None, None, None, None

# Saves payload from received frame to the output file. Exists only as a way to standardize code.
def save_payload(output_file, payload):
	output_file.write(payload)

MODE = sys.argv[1]
HOST = (sys.argv[2].split(":"))[0] if (MODE == "-c") else "127.0.0.1" #socket.gethostbyname(socket.getfqdn()) 
PORT = int((sys.argv[2].split(":"))[1]) if (MODE == "-c") else int(sys.argv[2])
ADDR = (HOST, PORT)

dcc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if MODE == "-c":
	dcc_socket.connect(ADDR)

else:
	dcc_socket.bind(ADDR)
	dcc_socket.listen(1)
	dcc_socket, client_address = dcc_socket.accept()

input_file  = open(sys.argv[3], "rb")
output_file = open(sys.argv[4], "wb")

max_payload_length = (2 ** 16) - 1

is_last_send = False
is_last_rcv  = True  # Maybe the other side has nothing to send
last_send_id = 1
cur_send_id  = 0
waiting_ack  = False
last_rcv_id  = 1
last_chksum  = 0
end_send     = False
end_rcv      = False

# send = [cur_frame_id, cur_frame, waiting_ack]
# receive = [last_frame_id, last_chksum]

try:
	# cria frame
	# salva frame em send
	# envia frame
	# troca waiting_ack para True
	# comeca timer de um segundo

	# checa se recebeu algo - se recebeu checa o frame
	# se receber o ack atualiza, checa o valor do id e se for o mesmo, atualiza cur_frame_id e reseta o timer
		# se o frame estiver ok checa o ID
			# se o id for o mesmo do ultimo e o checksum tambem, reenvia ack
			# se for diferente((last + 1) % 2) envia novo ack
			# atualiza last frame para id do frame recebido
	# se passar um segundo e nao receber o ack do envio, envia frame de novo e reseta o timer

	while True:
		# There is still data to send
		if not is_last_send and not waiting_ack:
			# Current ID has been updated since last sent frame
			if last_send_id != cur_send_id:
				cur_frame, is_last_send = create_frame(input_file, max_payload_length, cur_send_id, False)
				if is_last_send: end_send = True
				last_send_id = cur_send_id

			send_frame(dcc_socket, cur_frame)
			waiting_ack = True

			timer = time.time()
		
		# Check buffer for data
		payload, chksum, frame_id, is_last_rcv, is_ack = receive_frame(dcc_socket)
		if is_last_rcv: end_rcv = True

		# Last sent frame reception acknowledge
		if is_ack and frame_id == cur_send_id:
			cur_send_id = (cur_send_id + 1) % 2
			waiting_ack = False
			timer = -1
		# Frame has payload and is correct
		elif not payload is None: 
			# New frame
			if frame_id == (last_rcv_id + 1) % 2: 
				print "Saving payload"
				save_payload(output_file, payload)

				print "Updating registers"
				# Update registers with the information of the received frame  
				last_rcv_id = (last_rcv_id + 1) % 2 
				last_chksum = chksum

				# Create and send acknowledge message for the received frame
				ack = create_frame(input_file, max_payload_length, last_rcv_id, True)[0]
				send_frame(dcc_socket, ack)
			# Frame is a retransmission
			elif frame_id == last_rcv_id and chksum == last_chksum: 
				# Resend ack
				ack = create_frame(input_file, max_payload_length, last_rcv_id, True)[0]
				send_frame(dcc_socket, ack)

		print "end_rcv", end_rcv, "end_send", end_send, "waiting_ack", waiting_ack

		# End of communication. ACK for last received frame was already sent.
		if end_rcv and end_send and not waiting_ack: 
			break

		if timer != -1 and (time.time() - timer) >= 1:
			waiting_ack = False
			timer = -1

except socket.timeout:
	print >> sys.stderr, "Timeout no socket do cliente"

finally:
	input_file.close()
	output_file.close()
	dcc_socket.close()