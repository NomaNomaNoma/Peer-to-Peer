import socket
import sys
import json
import time
import os
import datetime
from peer_server import server_class
from peer_server import send_files
from fileSystem import fileSystem
from fileSystem import remove_peer
import make_files
import threading
import configparser

root_path = os.path.dirname(os.path.realpath(__file__))

chunks_path = os.path.join(root_path, 'chunks')
if not os.path.exists(chunks_path):
	os.makedirs(chunks_path)

files_path = './files/'


class query_indexer():
	def __init__(self):
		self.ci_server_host = 'localhost'
		self.ci_server_port = 5000
		self.ci_server_addr = (self.ci_server_host, self.ci_server_port)
		self.index_socket = None
		self.credentials = None
		self.GET_CREDENTIALS = json.dumps({'command':'register'})
		self.LIST_FILES = json.dumps({'command':'list_all_files'})
		self.SEARCH_FILES = {'command':'search'}

	def get_credentials(self):
		print '-'*80
		print 'Registering peer from tracker...'
		try:
			self.credentials = self.send_command_to_tracker(self.GET_CREDENTIALS)
			if self.credentials == 'error':
				raise
			self.credentials = int(self.credentials)
			return self.credentials
		except Exception as e:
			print 'Cannot register this peer.'
			print '-'*80

	def list_all_files(self):
		try:
			all_files = self.send_command_to_tracker(self.LIST_FILES)
			all_files = json.loads(all_files)
			print '-'*80
			print '\nThese are all files from the tracker: \n'

			for i,v in all_files.items():
				print '%s : %s' % (i, map(unicode.encode, v))
			print '-'*80
		except Exception as e:
			print 'Cannot get file list.'
			print e.message
			print '-'*80

	def search_files(self, file_name):
		print 'Searching the file from active peers...'
		time.sleep(1)
		try:
			self.SEARCH_FILES['filename'] = file_name
			search_command = json.dumps(self.SEARCH_FILES)
			search_file = self.send_command_to_tracker(search_command)
			search_results = json.loads(search_file)
			try:
				print '\nFollowing peers have the file: '
				for files in search_results[file_name]:
					print files,
				print ''
				return True
			except:
				print search_results
		except Exception as e:
			print 'File does not exist!'
			return False

	def create_existing_chunks(self):
		directory = os.listdir(chunks_path)
		chunks = []
		for chunk in directory:
			if chunk[-4:] == '.bin':
				chunks.append(chunk)
		config = configparser.ConfigParser()
		config.add_section('file')
		config.set('file', 'chunks_count', str(len(chunks)))
		config.add_section('chunks')
		for(i, chunks_hash) in enumerate(chunks):
			config.set('chunks', str(i), chunks_hash)
		with open(os.path.join(chunks_path, 'existing_chunks.ini'), 'w') as f:
			config.write(f)

	def add_to_tracker_list(self, filename):
		print 'Updating info to the tracker...'
		time.sleep(1)
		message = json.dumps({'command':'send', 'peer': credentials})
		peer_list = self.send_command_to_tracker(message)
		peer_list_result = json.loads(peer_list)
		print 'Update success!'
		print 'The tracker will now help to find if any other clients are downloading the same file...'
		time.sleep(1)
		print 'Right now following peers are downloading the same file: ' + str(peer_list_result)
		time.sleep(1)
		if len(peer_list_result) == 1:
			print 'You are the only one downloading this file now.'
		else:
			peer_list_result.remove(credentials)
			print 'Other peers: ' + str(peer_list_result) + ' are downloading now, getting chunks from them...'
			for i in range(0, len(peer_list_result)):
				ti = threading.Thread(target = self.connect_to_peer, args = (peer_list_result[i], filename))
				ti.start()
		pass

	def connect_to_peer(self, peer_id, filename):
		peer_connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		peer_connect_addr = ('localhost', int(peer_id))
		peer_connect.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		peer_connect.connect(peer_connect_addr)
		peer_connect.send('help'+ str(filename))
		recv_message = peer_connect.recv(1024)
		if recv_message == 'existing_chunks':
			self.create_existing_chunks()
			send_files('existing_chunks.ini', peer_connect)
			time.sleep(1)
		while True:
			size = peer_connect.recv(16)
			if not size:
				break
			size = int(size, 2)
			filename = peer_connect.recv(size)
			filesize = peer_connect.recv(32)
			filesize = int(filesize, 2)
			file_to_write = open(filename, 'wb')
			chunksize = 4096
			while filesize > 0:
				if filesize < chunksize:
					chunksize = filesize
				data = peer_connect.recv(chunksize)
				file_to_write.write(data)
				filesize -= len(data)
			file_to_write.close()
			if self.parse_config_file():
				time.sleep(1)
				peer_connect.close()
			print 'recevied chunks from ' + str(peer_id)
		print 'Peer Chunks downloaded!'
		peer_connect.close()


	def remove_from_tracker_list(self):
		print 'Removing from downloading client list...'
		time.sleep(1)
		message = json.dumps({'command':'delete', 'peer': credentials})
		self.send_command_to_tracker(message)
		print 'Remove success!'
		time.sleep(1)
		pass


	def send_command_to_tracker(self, cmd):
		try:
			self.index_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.index_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.index_socket.connect(self.ci_server_addr)
			self.index_socket.sendall(cmd)
			response = self.index_socket.recv(1024)
			return response

		except Exception as e:
			print 'Cannot send command to the tracker!'
			print '-'*80
			print e.message
			sys.exit(1)
			return 'error'

		finally:
			self.index_socket.close()

	def receive_from_tracker(self, sock):
		sock.send('OK')
		condition = 1
		while condition:
			size = sock.recv(16)
			if not size:
				break
			size = int(size, 2)
			filename = sock.recv(size)
			filesize = sock.recv(32)
			filesize = int(filesize, 2)
			file_to_write = open(filename, 'wb')
			chunksize = 4096
			while filesize > 0:
				if filesize < chunksize:
					chunksize = filesize
				data = sock.recv(chunksize)
				file_to_write.write(data)
				filesize -= len(data)
			file_to_write.close()
			if self.parse_config_file():
				time.sleep(1)
				print 'Chunks downloaded!'
				print 'Creating File...'
				sock.close()
				condition = 0
				make_files.makeFiles()
			print 'recevied chunks from origin server'

	def parse_config_file(self):
		config = configparser.ConfigParser()
		config.read(os.path.join(chunks_path, 'file.ini'))
		self.filename = config.get('file', 'name')
		chunks_count = config.getint('file', 'chunks_count')
		self.chunks = [config.get('chunks', str(i)) for i in range(chunks_count)]
		for chunks in self.chunks:
			if not os.path.exists(os.path.join(chunks_path, chunks + '.bin')):
				return False
		return True

if __name__ == '__main__':

	print '-'*80

	try:
		qi = query_indexer()
	except Exception as e:
		print 'Failed to access query!'
		print '-'*80
		sys.exit(1)

	credentials = qi.get_credentials()

	if credentials == 'error':
		print 'Tracker is not running, please start the tracker first!'
		print '-'*80
		sys.exit(1)

	try:
		print 'Setting peer as a server...'
		peer_server = server_class(credentials)
		peer_server.daemon = True
		peer_server.start()
		time.sleep(1)
		print 'Peer server started!\n'
	except Exception as e:
		print 'Peer server cannot be started'
		print e.message
		print '-'*80
		sys.exit(1)

	try:
		print 'Start file monitor system...'
		file_system = fileSystem(files_path, credentials)
		file_system.daemon = True
		file_system.start()
		time.sleep(1)
		print 'File monitor system started!'
	except Exception as e:
		print 'File system cannot be started!\n'
		print e.message
		print '-'*80
		sys.exit(1)

	print 'Tracker is running on port : 5000'
	print 'You are running on port    : %d' % credentials

	try:
		choices = [1,2,3]
		print '-'*80
		while 1:
			time.sleep(1)
			print '\nEnter your choice.\n'
			print '1 - List all the files.'
			print '2 - Search files.'
			print '3 - Download files.'

			print '\nPress ctrl + c to shutdown this peer.'

			command = raw_input()
			if int(command) not in choices:
				print 'Invalid, please enter again.\n'
				continue
			print '-'*80
			print 'You have chose: %d \n' % int(command)
			time.sleep(1)

			if int(command) == 1:
				qi.list_all_files()
			elif int(command) == 2:
				print 'Enter file name:'
				file_name = raw_input()
				#file_name = file_name.lower()
				qi.search_files(file_name)
			elif int(command) == 3:
				print 'Enter the file you want:'
				file_name = raw_input()
				#file_name = file_name.lower()
				time.sleep(1)
				if not qi.search_files(file_name):
					print 'Please try again.'
					continue
				print 'From which peer you want to download?'
				peer_transfer_id = raw_input()
				peer_addr = ('localhost', int(peer_transfer_id))
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				s.connect(peer_addr)
				if file_name != 'q':
					s.send(file_name)
					data = s.recv(1024)
					if data[:6] == 'EXISTS' :
						filesize = long(data[6:])
						time.sleep(1)
						message = raw_input("File is " + str(filesize/(1024*1024)) + \
							"Mbs, downloaded? (Y/N)? ->")
						if message == 'Y':
							os.chdir(chunks_path)
							time.sleep(1)
							print '-'*80
							print 'Changing direction caused file system daemon error... \nNothing hurts, please ignore...'
							print '-'*80
							print 'Downloading chunks...'
							print 'Start downloading!'
							t1 = threading.Thread(target = qi.add_to_tracker_list, args=(file_name,))
							t2 = threading.Thread(target = qi.receive_from_tracker, args=(s,))
							t1.start()
							t2.start()

							t1.join()
							t2.join()
							qi.remove_from_tracker_list()



					else:
						print "File does not Exists!"

					s.close()

	except Exception as e:
		print e.message
	except KeyboardInterrupt:
		remove_peer(int(credentials))
		print '-'*78
		print 'Shutting down this peer!'
		print '-'*80
		time.sleep(1)
		sys.exit(1)
	finally:
		peer_server.close()