import os
import sys
import configparser

root_path = os.path.dirname(os.path.realpath(__file__))
chunks_path = os.path.join(root_path, 'chunks')

saved_file_path = os.path.join(root_path,'files')
if not os.path.exists(saved_file_path):
	os.makedirs(saved_file_path)

class makeFiles:

	def __init__(self):
		if self.parse_config_file(): #make sure has received all chunks
			self.make_file()
			print('File downloaded.')
		else:
			print('Cannot download file, please download again.')


	def parse_config_file(self):
		config = configparser.ConfigParser()
		config.read(os.path.join(chunks_path, 'file.ini'))
		self.filename = config.get('file', 'name')
		chunks_count = config.getint('file', 'chunks_count')
		self.chunks = [config.get('chunks', str(i)) for i in range(chunks_count)]
		for chunks in self.chunks:
			if not os.path.exists(os.path.join(chunks_path, chunks + '.bin')):
				print('Missing chunks, please download again.')
				return False
		return True

	def make_file(self):
		with open(os.path.join(saved_file_path,self.filename),'wb') as f:
			for chunk in self.chunks:
				with open(os.path.join(chunks_path,chunk + '.bin'), 'rb') as h:
					chunks_content = h.read()
					f.write(chunks_content)
		self.remove_chunks()

	def remove_chunks(self):
		for file in os.listdir(chunks_path):
			if file[-4:] == ".bin":
				os.remove(os.path.join(chunks_path, file))
		print("Chunks have been removed.")


if __name__ == '__main__':
    makeFiles()