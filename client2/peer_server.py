import socket
import sys
import threading
import time
import os
import math
import hashlib
import configparser

HOSTNAME = 'localhost'

CHUNK_SIZE = 1024 * 1024

root_path = os.path.dirname(os.path.realpath(__file__))

files_path = os.path.join(root_path, 'files')
if not os.path.exists(files_path):
	os.makedirs(files_path)

chunks_path = os.path.join(root_path, 'chunks')
if not os.path.exists(chunks_path):
	os.makedirs(chunks_path)

clients = []
origin_port = ''

def RetrFile(name, sock):
	filename = sock.recv(1024)
	filepath = os.path.join(files_path, filename)
	if os.path.exists(filepath):
		sock.send("EXISTS " + str(os.path.getsize(filepath)))
		userResponse = sock.recv(1024)
		if userResponse[:2] == 'OK':
			ip, port = sock.getpeername()
			print "-"*80
			print "Client " + str(port) + " wants the file " + str(filename)

			print "Making chunks..."
			make_chunks(filename, filepath)
			print "Chunks made!"

			directory = os.listdir(chunks_path)
			print "Sending config files..."
			send_files('file.ini', sock)
			print "Config files sent!"

			global origin_port
			if origin_port == '':
				origin_port = port
				print "Sending chunks..."
				for chunks in directory:
					if chunks[-4:] == '.bin' :
						filename = chunks
						send_files(filename, sock)

			elif port != origin_port:
				print "There are other clients downloading this file, sending different chunks..."
				for chunks in reversed(directory):
					if True:
						filename = chunks
						send_files(filename, sock)

			print "Chunks Sent!"
	else:
		sock.send("ERR")

	sock.close()






def make_chunks(filename, filepath):
	remove_existing_chunks()
	chunks = []
	chunks_count = math.ceil(os.path.getsize(filepath) / CHUNK_SIZE)
	with open(filepath, 'rb') as f:
		while 1:
			chunks_content = f.read(CHUNK_SIZE)
			if len(chunks_content) == 0:
				break
			chunks_hash = hashlib.sha1(chunks_content).hexdigest()
			chunks.append(chunks_hash)
			#put chunks into folder:
			with open(os.path.join(chunks_path,chunks_hash + '.bin'), 'wb') as h:
				h.write(chunks_content)
	create_config_file(filename, chunks)


#if there is already chunks in the file, remove and re-create it.
def remove_existing_chunks():
	for file in os.listdir(chunks_path):
		if file[-4:] == '.bin':
			os.remove(os.path.join(chunks_path,file))


#create a config file for receiver to check no chunk missing.
def create_config_file(filename, chunks):
	config = configparser.ConfigParser()
	config.add_section('file')
	config.set('file','name',filename)
	config.set('file','chunks_count',str(len(chunks)))
	config.add_section('chunks')
	for (i, chunks_hash) in enumerate(chunks):
		config.set('chunks', str(i), chunks_hash)
	with open(os.path.join(chunks_path, 'file.ini'), 'w') as f:
		config.write(f)


def send_files(filename, sock):
	print filename
	size = len(filename)
	size = bin(size)[2:].zfill(16) # encode filename size as 16 bit binary
	sock.send(size)
	sock.send(filename)

	filename = os.path.join(chunks_path,filename)
	size = os.path.getsize(filename)
	size = bin(size)[2:].zfill(32) # encode filesize as 32 bit binary
	sock.send(size)

	file_to_send = open(filename, 'rb')

	l = file_to_send.read()
	sock.sendall(l)
	file_to_send.close()
	print 'sent!'
	time.sleep(1)		







class server_class(threading.Thread):
	def __init__(self, port):
		super(server_class, self).__init__()
		self.PORT = port
		self.server = None
		self.threads = []

	def process_data(self):
		client_connection = None

		while True:
			try:
				self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.server.bind((HOSTNAME, self.PORT))
				self.server.listen(10)

				client_connection, client_addr = self.server.accept()

				if client_addr not in clients:
					clients.append(client_addr)

				if client_connection:
					print 'Connect peer success! From %s on port: %d' % (client_addr[0], client_addr[1])
					t =threading.Thread(target=RetrFile, args=("retrThread", client_connection))
					t.start()

			except Exception as e:
				print '-'*80
				print 'Processing Error!'
				print e.message
				print '\nShutting down...'
				sys.exit(1)
				raise

			finally:
				self.server.close()

	def close(self):
		self.server.close()

	def run(self):
		self.process_data()		