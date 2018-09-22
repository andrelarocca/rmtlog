import sys
import socket
import time
import data_link_utils

FILE = sys.argv[1]  # File to read log messages
HOST = (sys.argv[2].split(":"))[0]
PORT = int((sys.argv[2].split(":"))[1])
WTX = int(sys.argv[3]) # Transmission window size
TOUT = int(sys.argv[4]) # TImeout
PERROR = int(sys.argv[5]) # Error probability

ADDR = (HOST, PORT)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.connect(ADDR)
client_socket.settimeout(1) # Socket timeout 1s

input_file  = open(FILE, "rb")

max_payload_length = (2 ** 16) - 1  # Greatest number of bytes that the length field can address

is_last_send = False # Marks the end of the input file and thus the creation of the last frame
is_last_rcv  = True  # Reception of the data frame with end flag. Starts as True because the other side may have nothing to send.
last_send_id = 1     # ID of the last sent frame. Begins at one to prevent last_send_id == cur_send_id
cur_send_id  = 0     # ID of the actual frame: being sent or waiting for ACK
waiting_ack  = False # Last frame is waiting for ACK response
last_rcv_id  = 1     # ID of the last received frame. Begins at one to show that the first frame should have id 0.
last_chksum  = 0     # chksum from last frame 
end_send     = False # If the last frame was already sent, save it to mark the end of data transmission
end_rcv      = False # If the last frame was already received, save it to mark the end of data reception

while True:
	try:
		if not is_last_send and not waiting_ack:  # There is still data to send
			if last_send_id != cur_send_id:  # Last frame was confirmed with ACK
				# Create next frame with data from the input file
				cur_frame, is_last_send = data_link_utils.create_frame(input_file, max_payload_length, cur_send_id, False)
				if is_last_send: end_send = True 
				last_send_id = cur_send_id 

			data_link_utils.send_frame(client_socket, cur_frame)
			waiting_ack = True 

			timer = time.time()  # Timer that will "wait" for 1 second before retransmission

		# Check buffer for data
		payload, chksum, frame_id, is_last_rcv, is_ack = data_link_utils.receive_frame(client_socket)
		if is_last_rcv: end_rcv = True

		if is_ack and frame_id == cur_send_id: # ACK for last sent frame has arrived
			cur_send_id = (cur_send_id + 1) % 2  # New frame id
			waiting_ack = False  # Can transmit a new frame
			timer = -1  # Reset timer
		elif not payload is None:  # Frame has payload and is correct
			if frame_id == (last_rcv_id + 1) % 2:  # New frame
				#Saves received data to output file
				data_link_utils.save_payload(output_file, payload)  

				# Update registers with the information of the received frame  
				last_rcv_id = (last_rcv_id + 1) % 2 
				last_chksum = chksum

				# Create and send acknowledge message for the received frame
				ack = data_link_utils.create_frame(input_file, max_payload_length, last_rcv_id, True)[0]
				data_link_utils.send_frame(client_socket, ack)
			elif frame_id == last_rcv_id and chksum == last_chksum:  # Frame is a retransmission
				# Resend ack for last received frame
				ack = data_link_utils.create_frame(input_file, max_payload_length, last_rcv_id, True)[0]
				data_link_utils.send_frame(client_socket, ack)

		# End of communication. ACK for last received frame was already sent.
		if end_rcv and end_send and not waiting_ack:
			print "End of communication" 
			break

		# Timer(1 second) is over and no ACK was received. We need to retransmit the frame.
		if timer != -1 and (time.time() - timer) >= 1:
			waiting_ack = False  # Retransmit ack
			timer = -1  # Reset timer

	except socket.timeout:  # 1 second has been passed in the blocking receive. If is waiting for ack, retransmit last frame.
		if waiting_ack:
			print "Timeout. Retransmiting frame\n"
			data_link_utils.send_frame(client_socket, cur_frame)
			timer = time.time()  # Reset timer

input_file.close()
output_file.close()
client_socket.close()