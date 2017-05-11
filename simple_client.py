import socket
import struct
import time

HOST = "127.0.0.1" # Endereco IP do servidor
PORT = 51515 # Porta na qual o servidor vai escutar
ADDR = (HOST, PORT)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Inicializa o socket
client_socket.connect(ADDR)

client_socket.sendall("a")
client_socket.sendall("b")
client_socket.sendall("c")

client_socket.close()