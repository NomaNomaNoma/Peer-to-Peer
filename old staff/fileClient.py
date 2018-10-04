import socket
import make_files
import os


root_path = os.path.dirname(os.path.realpath(__file__))

chunks_path = os.path.join(root_path, 'chunks')
if not os.path.exists(chunks_path):
	os.makedirs(chunks_path)

def Main():

	HOSTNAME = 'localhost'
	PORT = 5000

	s = socket.socket()
	s.connect((HOSTNAME, PORT))

	filename = raw_input("Filename? -> ")
	if filename != 'q':
		s.send(filename)
		data = s.recv(1024)
		if data[:6] == 'EXISTS' :
			filesize = long(data[6:])
			message = raw_input("File Exists, " + str(filesize/(1024*1024)) + \
				"Mbs, downloaded? (Y/N)? ->")
			if message == 'Y':
				s.send('OK')
				os.chdir(chunks_path)
				while True:
				    size = s.recv(16)
				    if not size:
				        break
				    size = int(size,2)
				    filename = s.recv(size)
				    filesize = s.recv(32)
				    filesize = int(filesize, 2)
				    file_to_write = open(filename, 'wb')
				    chunksize = 4096
				    while filesize > 0:
				        if filesize < chunksize:
				            chunksize = filesize
				        data = s.recv(chunksize)
				        file_to_write.write(data)
				        filesize -= len(data)

				    file_to_write.close()
				print "Chunks downloaded! "

				print "Creating File..."
				make_files.makeFiles()

		else:
			print "File does not Exists!"
	s.close()

if __name__ == '__main__':
	Main()