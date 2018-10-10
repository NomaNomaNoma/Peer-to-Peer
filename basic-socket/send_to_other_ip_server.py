#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import os

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("", 12345)) #if the clients/server are on different network you shall bind to ('', port)

s.listen(10)
c, addr = s.accept()
print('{} connected.'.format(addr))

f = open("image.png", "rb")
l = os.path.getsize("image.png")
m = f.read(l)
c.sendall(m)
f.close()
print("Done sending...")