#!/usr/bin/env python
import socket
import struct
import json
import argparse
import base64
     
class McIcons:
	def __init__(self, host, port=25565):
		self.host = host
		self.port = port
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def unpack_varint(self):
		i = 0
		for j in range(5):
			a = ord(self.s.recv(1))
			i |= (a & 0x7F) << 7*j
			if not a & 0x80:
				break
		return i

	def pack_varint(self, paramInt):
		buff = ""
		while True:
			i = paramInt & 0x7F
			paramInt >>= 7
			buff += struct.pack("B", i | (0x80 if paramInt > 0 else 0))
			if paramInt == 0:
				break
		return buff

	def pack_data(self, paramString):
		return self.pack_varint(len(paramString)) + paramString

	def pack_short(self, paramShort):
		return struct.pack('>H', paramShort)

	def connect(self):
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.connect((self.host, self.port))

	def close(self):
		self.s.close() 

	def send_handshake_packet(self, payload):
		self.s.send(self.pack_data("\x00\x04" + self.pack_data(self.host.encode('utf8')) + self.pack_short(self.port) + payload))

	def send_request_packet(self):
		self.s.send(self.pack_data("\x00"))

	def read_response_packet(self):
		length = self.unpack_varint()
		packetid = self.unpack_varint()
		string_length = self.unpack_varint()
		string = ""
		while len(string) < string_length:
			string += self.s.recv(1)
		return string

def main():
	argparser = argparse.ArgumentParser()
	argparser.add_argument("host", help="Hostname", type=str)
	argparser.add_argument("--port", "-p", help="Port", type=int)
	args = argparser.parse_args()

	mcIcons = None 
	if args.port:
		mcIcons = McIcons(args.host, args.port)
	else:
		mcIcons = McIcons(args.host)
	mcIcons.connect()
	print("Connected!")
	mcIcons.send_handshake_packet("\x01")
	mcIcons.send_request_packet()
	print("Sent handshake and request packets.")
	iconString = json.loads(mcIcons.read_response_packet())['favicon'].replace("data:image/png;base64,", "")
	print("Decrypting icon...")
	iconImage = base64.decodestring(iconString)
	iconFile = open(args.host.replace(".", "-") + ".png", 'wb')
	iconFile.write(iconImage)
	iconFile.close()
	print("Icon downloaded.")

if __name__ == "__main__": main()
