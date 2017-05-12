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

# PARA EXECUTAR
# Socket com abertura passiva: python dcc023c2.py -s <PORT> <INPUT> <OUTPUT>
# Socket com abertura ativa: python dcc023c2.py -c <IP>:<PORT> <INPUT> <OUTPUT>
#
# Para executarmos o script diretamente(assim como em C):
# chmod +x ./dcc023c2
# ./dcc023c2 argc[]

""" TODO
 - Separar em main e lib dccnet
 - Talvez tenhamos que fazer loop para receber em receive_frame
 - Detectar fechamento de socket
 - receive nao pode ser blocante senao o socket pode ficar travado em rcv ate o timeout
"""

""" DUVIDAS
 - Socket passivo tem que morrer ou continua esperando novas conexoes? MORRER
 - Checar se socket.rcv(0) buga - NAO BUGA, retorna ""
 - Checksum e realizado com ou sem os packs?
"""

import sys
import socket
import time
import data_link_utils

MODE = sys.argv[1]
HOST = (sys.argv[2].split(":"))[0] if (MODE == "-c") else socket.gethostbyname(socket.getfqdn()) 
PORT = int((sys.argv[2].split(":"))[1]) if (MODE == "-c") else int(sys.argv[2])
ADDR = (HOST, PORT)

dcc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if MODE == "-c":
	dcc_socket.connect(ADDR)
else:
	dcc_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Prevents "Address already in use" error
	dcc_socket.bind(ADDR)
	dcc_socket.listen(1)
	dcc_socket = dcc_socket.accept()[0]

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
	dcc_socket.settimeout(10)
	# cria frame
	# guarda frame em cur_frame
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
			# Current ID has been updated since last sent frame(ACK for that frame was received)
			if last_send_id != cur_send_id:
				cur_frame, is_last_send = data_link_utils.create_frame(input_file, max_payload_length, cur_send_id, False)
				if is_last_send: end_send = True
				last_send_id = cur_send_id

			data_link_utils.send_frame(dcc_socket, cur_frame)
			waiting_ack = True

			timer = time.time()
		# Check buffer for data
		payload, chksum, frame_id, is_last_rcv, is_ack = data_link_utils.receive_frame(dcc_socket)
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
				data_link_utils.save_payload(output_file, payload)

				# Update registers with the information of the received frame  
				last_rcv_id = (last_rcv_id + 1) % 2 
				last_chksum = chksum

				# Create and send acknowledge message for the received frame
				ack = data_link_utils.create_frame(input_file, max_payload_length, last_rcv_id, True)[0]
				data_link_utils.send_frame(dcc_socket, ack)
			# Frame is a retransmission
			elif frame_id == last_rcv_id and chksum == last_chksum: 
				# Resend ack
				ack = data_link_utils.create_frame(input_file, max_payload_length, last_rcv_id, True)[0]
				data_link_utils.send_frame(dcc_socket, ack)

#		print "end_rcv", end_rcv, "end_send", end_send, "waiting_ack", waiting_ack
#		print

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