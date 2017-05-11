import socket
import struct

HOST = "127.0.0.1" # Endereco IP do servidor
PORT = 51515 # Porta na qual o servidor vai escutar
ADDR = (HOST, PORT)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Inicializa o socket
server_socket.bind(ADDR) # Associa o socket ao endereco e a porta especificados
server_socket.listen(1) # Espera por apenas uma conexao antes de recusar outros pedidos

while True:
	client_socket, client_address = server_socket.accept() # Fica travado no accept ate receber uma nova conexao

	print client_socket.recv(1).decode()

	client_socket.close
