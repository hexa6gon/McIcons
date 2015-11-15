#!/usr/bin/env python
import socket
import struct
import json
import argparse
import base64
import os

class McIcons:
	def __init__(self, host, port=25565):
		self.host = host
		self.port = port
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def _unpack_varint(self):
		i = 0
		for j in range(5):
			a = ord(self.s.recv(1))
			i |= (a & 0x7F) << 7*j
			if not a & 0x80:
				break
		return i

	def _pack_varint(self, paramInt):
		buff = ""
		while True:
			i = paramInt & 0x7F
			paramInt >>= 7
			buff += struct.pack("B", i | (0x80 if paramInt > 0 else 0))
			if paramInt == 0:
				break
		return buff

	def _pack_data(self, paramString):
		return self._pack_varint(len(paramString)) + paramString

	def _pack_short(self, paramShort):
		return struct.pack('>H', paramShort)

	def connect(self):
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.connect((self.host, self.port))

	def close(self):
		self.s.close() 

	def send_handshake_packet(self, protocol_version, payload):
		packet = self._pack_data("\x00" + protocol_version + self._pack_data(self.host.encode('utf8')) + self._pack_short(self.port) + payload)
		self.s.send(packet)
		return len(packet)

	def send_request_packet(self):
		packet = self._pack_data("\x00")
		self.s.send(packet)
		return len(packet)

	def read_response_packet(self):
		length = self._unpack_varint()
		packetid = self._unpack_varint()
		string_length = self._unpack_varint()
		string = ""
		while len(string) < string_length:
			string += self.s.recv(1)
		return {'length' : int(length), 'string' : string}

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
	handshakeLen = mcIcons.send_handshake_packet("\x04", "\x01")
	requestLen = mcIcons.send_request_packet()
	print("Sent handshake (" + str(handshakeLen) + " bytes) and request (" + str(requestLen) + " bytes) packets.")
	response = mcIcons.read_response_packet()
	responseLen = response['length']
	iconJson = json.loads(response['string'])
	print("Readed JSON response (" + str(responseLen) + " bytes).")
	iconImage = ""
	if "data:image/png;base64," not in json.dumps(iconJson):
		print("Icon not found.")
		mcIcons.close()
		print("Connection closed.")
		exit(1)
	else:
		iconImage = base64.decodestring(iconJson['favicon'].replace("data:image/png;base64,", ""))
	print("Decrypted icon.")
	iconFile = open(args.host.replace(".", "-") + ".png", 'wb')
	iconFile.write(iconImage)
	print("Icon downloaded to: " + os.path.abspath(args.host.replace(".", "-") + ".png"))
	iconFile.close()
	mcIcons.close()
	print("Connection closed.")

if __name__ == "__main__": main()
