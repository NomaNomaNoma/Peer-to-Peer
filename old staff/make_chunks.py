import sys
import os
import math
import hashlib
import configparser

CHUNK_SIZE = 1024 * 1024 #1MB/chunk

root_path = os.path.dirname(os.path.realpath(__file__))

files_path = os.path.join(root_path, 'files')
if not os.path.exists(files_path):
	os.makedirs(files_path)

chunks_path = os.path.join(root_path, 'chunks')
if not os.path.exists(chunks_path):
	os.makedirs(chunks_path)

config_path = os.path.join(root_path, 'config')
if not os.path.exists(config_path):
	os.makedirs(config_path)

class makeChunks:

	def __init__(self):
		self.check_input()
		self.make_chunks()
		self.create_config_file()
		print('Done')

	def check_input(self):
		self.filename = sys.argv[0]
		self.filepath = os.path.join(files_path, self.filename)

	def make_chunks(self):
		if not os.path.exists(self.filepath):
			print("No such file exists. Please put the file in 'files' folder under root.")
			sys.exit(1)
		self.remove_existing_chunks()
		self.chunks = []
		chunks_count = math.ceil(os.path.getsize(self.filepath) / CHUNK_SIZE)
		with open(self.filepath, 'rb') as f:
			while 1:
				chunks_content = f.read(CHUNK_SIZE)
				if len(chunks_content) == 0:
					break
				chunks_hash = hashlib.sha1(chunks_content).hexdigest()
				self.chunks.append(chunks_hash)
				#put chunks into folder:
				with open(os.path.join(chunks_path,chunks_hash + '.bin'), 'wb') as h:
					h.write(chunks_content)

	#if there is already chunks in the file, remove and re-create it.
	def remove_existing_chunks(self):
		for file in os.listdir(chunks_path):
			if file[-4:] == '.bin':
				os.remove(os.path.join(chunks_path,file))

	#create a config file for receiver to check no chunk missing.
	def create_config_file(self):
		config = configparser.ConfigParser()
		config.add_section('file')
		config.set('file','name',self.filename)
		config.set('file','chunks_count',str(len(self.chunks)))
		config.add_section('chunks')
		for (i, chunks_hash) in enumerate(self.chunks):
			config.set('chunks', str(i), chunks_hash)
		with open(os.path.join(config_path, 'file.ini'), 'w') as f:
			config.write(f)

if __name__ == '__main__':
    makeChunks()

