import socket
import struct

HOST = "127.0.0.1" # Endereco IP do servidor
PORT = 51515 # Porta na qual o servidor vai escutar
ADDR = (HOST, PORT)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Inicializa o socket
client_socket.connect(ADDR)

client_socket.sendall("x")

client_socket.close()