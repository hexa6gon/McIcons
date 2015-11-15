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
			try:
				a = ord(self.s.recv(1))
				i |= (a & 0x7F) << 7*j
				if not a & 0x80:
					break
			except:
				print("Server not responding.")
				self.close()
				print("Connection closed.")
				exit(1)
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
		try:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.s.connect((self.host, self.port))
		except:
			print("Cannot connect to " + self.host + ":" + str(self.port))
			exit(1)

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

def get_valid_port():
	port = 0
	try:
		inp = raw_input('Enter port (if you want 25565 please press enter): ')
		if inp == "":
			return 25565
		port = int(inp)
	except ValueError:
		print("Please enter a number.")
		port = get_valid_port()
	return port

def get_valid_hostname():
	hostname = raw_input('Enter hostname: ').replace(" ", "")
	while not hostname:
		print("Please enter a valid hostname.")
		hostname = raw_input('Enter hostname: ')
	return hostname

def main():
	argparser = argparse.ArgumentParser()
	argparser.add_argument("--host", "-H", help="Hostname", type=str)
	argparser.add_argument("--port", "-p", help="Port", type=int)
	args = argparser.parse_args()

	mcIcons = None
	hostname = ""
	port = 0
	if args.host:
		hostname = args.host
	else:
		hostname = get_valid_hostname()
	if args.port:
		port = args.port
	else:
		port = get_valid_port()
	mcIcons = McIcons(hostname, port)
	mcIcons.connect()
	print("Connected!")
	handshakeLen = mcIcons.send_handshake_packet("\x04", "\x01")
	requestLen = mcIcons.send_request_packet()
	print("Sent handshake (" + str(handshakeLen) + " bytes) and request (" + str(requestLen) + " bytes) packets.")
	response = mcIcons.read_response_packet()
	responseLen = response['length']
	iconJson = None
	try:
		iconJson = json.loads(response['string'])
	except:
		print("Response is invalid (json parser cannot parse this response).")
		exit(1)
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
	iconFile = open(hostname.replace(".", "-") + ".png", 'wb')
	iconFile.write(iconImage)
	print("Icon downloaded to: " + os.path.abspath(hostname.replace(".", "-") + ".png"))
	iconFile.close()
	mcIcons.close()
	print("Connection closed.")

if __name__ == "__main__": main()
