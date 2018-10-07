import socket
import time
import threading
import json
import os
import sys

HOSTNAME = 'localhost'
PORT = 5000
BUFFER = 65536

peer = []
download_peer = []

class tracker_class():
	def __init__(self):
		self.server = None
		self.threads = []
		self.file_index = {}
		self.peer_init_port = 6000
		self.peer_list = []

	def register_peer(self):
		if (len(self.peer_list)) != 0:
			port_no = max(self.peer_list) + 1;
			self.peer_list.append(port_no)
			return str(port_no)
		else:
			self.peer_list.append(self.peer_init_port)
			return str(self.peer_init_port)

	def index(self, request):
		for i,v in request.items():
			if i == 'command':
				pass
			else:
				if type(v) == list:
					for sub_f in v:
						#sub_f = sub_f.lower()
						if sub_f in self.file_index.keys():
							self.file_index[sub_f].append(i)
						else:
							self.file_index[sub_f] = []
							self.file_index[sub_f].append(i)

				elif type(v) == tuple:
					files_added = v[0]
					files_deleted = v[1]
					if len(files_added) != 0:
						for subs in files_added:
							#subs = subs.lower()
							if subs in self.file_index.keys():
								self.file_index[subs].append(i)
							else:
								self.file_index[subs] = []
								self.file_index[subs].append(i)
					if len(files_deleted) != 0:
						for subs in files_deleted:
							#subs = subs.lower()
							self.file_index[subs].pop(self.file_index.index(i))

	def search(self,request):
		file_name = request['filename']
		if file_name in self.file_index.keys():
			return json.dumps({file_name:self.file_index[file_name]})
		else:
			return 'File not found in the index.'  

	def list_all_files(self):
		return json.dumps(self.file_index)

	def remove_peer(self,peer):
		for i,v in self.file_index.items():
			if unicode(peer) in v:
				v.pop(v.index(unicode(peer)))

	def process_request(self):
		client_connection = None
		print '-'*80
		print 'Server started on port: ' + str(PORT)
		print 'Press ctrl + c to shutdown server.'
		print 'Waiting for clients...'
		print '-'*80
		infinite = 1

		while infinite:
			try:
				self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.server.bind((HOSTNAME, PORT))
				self.server.listen(10)

				client_connection, client_addr = self.server.accept()
				if client_connection:
					print 'Client connected from %s on port: %d' % (client_addr[0], client_addr[1])
					request = client_connection.recv(BUFFER)
					req = json.loads(request)
					command = req['command']

					if command == 'index':
						self.index(req)
					elif command == 'register':
						print 'Registering peer...'
						peer_id = self.register_peer()
						peer.append(peer_id)
						client_connection.sendall(peer_id)
						print 'Success! Peer is now connected on the tracker!'
						print 'There are ' + str(len(peer)) + ' clients now: ' + str(peer)
					elif command == 'list_all_files':
						print 'Sending file list to peers...'
						all_files = self.list_all_files()
						client_connection.sendall(all_files)
						print 'File list sent!'
					elif command == 'remove':
						peer_id = req['peer']
						print 'Removing peer...'
						peer.remove(str(peer_id))
						time.sleep(1)
						self.remove_peer(peer_id)
						print 'Peer %d removed!' % peer_id
						print 'There are ' + str(len(peer)) + ' clients now: ' + str(peer)
					elif command == 'search':
						search_results = self.search(req)
						print 'Sending search results...'
						client_connection.sendall(search_results)
						print 'Search results sent!'
					elif command == 'send':
						print 'Adding client to the downloading list...'
						peer_id = req['peer']
						download_peer.append(peer_id)
						time.sleep(1)
						print 'Add success!'
						print 'Now downloading clients are ' + str(download_peer)
						client_connection.sendall(str(download_peer))
					elif command == 'delete':
						print 'Removing client from the downloading list...'
						peer_id = req['peer']
						download_peer.remove(peer_id)
						time.sleep(1)
						print 'Remove success!'
						print 'Now downloading clients are ' + str(download_peer)
						client_connection.send('remove success!')
					else:
						pass

			except KeyboardInterrupt:
				infinite = 0
				print '-'*78
				print 'Shutting down Peer Server!'
				print '-'*80
				sys.exit(1)

			except Exception as e:
				print '-'*80
				print 'Processing Error!'
				print e.message
				print ''
				sys.exit(1)
				raise

			finally:
				self.server.close()

	def close(self):
		self.server.close()

	def run(self):
		self.process_request()


if __name__ == '__main__':
	try:
		cs = tracker_class()
		cs.run()
	except KeyboardInterrupt:
		print '-'*78
		print '\nKeyboard Interrupt Caught.!'
		print 'Shutting Down Peer Server..!!!'
		print '-'*80
		cs.close()
		sys.exit(1)