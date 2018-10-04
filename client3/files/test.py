import sys
import threading
import os
import time
import socket
import json

class fileSystem(threading.Thread):
	def __init__(self, monitor_dir, peer_id):
		try:
			super(fileSystem, self).__init__()
			self.tracker_addr = ('localhost', 5000)
			self.monitor_dir = monitor_dir
			self.files = []
			self.current_directory = './files'
			self.peer_id = peer_id
			self.connection = None

		except socket.error as e:
			print 'Tracker is down!'
			sys.exit(1)

	def monitor(self):
		while 1:
			if len(self.files) != 0:
				self.files.sort()
				cur_files = os.listdir(self.current_directory)
				cur_files.sort()
				if cur_files == self.files:
					pass
				else:
					changes_added = list(set(cur_files) - set(self.files))
					changes_removed = list(set(self.files) - set(cur_files))
					self.registry(changes, self.peer_id)

			else:
				self.files = os.listdir(self.current_directory)
				self.registry(self.files, self.peer_id)

			time.sleep(2)

	def registry(self, changes, peer_id):
		to_send = {peer_id: changes, 'command': 'index'}
		to_send = json.dumps(to_send)
		try:
			self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.connection.connect(self.tracker_addr)
			self.connection.sendall(to_send)
		except Exception as e:
			print 'Cannot connect to the tracker!'
			print '*'*80

	def run(self):
		self.monitor()

class remove_peer():
	def __init__(self, peer_id):
		self.tracker_addr = ('localhost', 5000)
		self.remove = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.remove.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.remove.connect(self.tracker_addr)
		self.remove_cmd = {'command':'destroy','peer':peer_id}
		self.destroy_peer(self.remove_cmd)

	def destroy_peer(self, remove_cmd):
		print 'Removing peer...'
		remove_cmd = json.dumps(remove_cmd)
		self.remove.sendall(remove_cmd)








