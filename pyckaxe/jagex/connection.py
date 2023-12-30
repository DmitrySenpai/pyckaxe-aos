"""
Copyright (c) mari_kiri, 2013.

This file is part of Pyckaxe.

Pyckaxe is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Pyckaxe is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Pyckaxe.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Connection to an Ace of Spades 1.x server

Yes, there is a lot of redundancy. We can refactor this where necessary.
"""

from pyckaxe.constants import *
from pyckaxe.util import *
from pyckaxe.jagex.constants import *
from pyckaxe.reactor import reactor
import pyckaxe.jagex.lzf as lzf
import enet
import struct
import time

class JagexConnection:
	"""
	Necessary state for an Ace of Spades 1.x connection.
	To avoid OO-fuelled redundancy, this also holds the player state.
	"""
	def __init__(self, server, peer, player_id, **kwargs):
		"""
		server is the JagexServer instance you wish to bind this connection to.
		peer is the ENet peer this connection pertains to.
		player_id is the ID of this player.
		"""
		self.server = server
		self.peer = peer
		self.player_id = player_id

		self.team = -1
		self.cls = -1
		self.team_next = -1
		self.cls_next = -1
		self.bcolor = [127, 127, 127]
		self.name = "<unnamed>"

		self.has_registered = False
		self.in_game = False

		self.alive = True

		self.steam_key = ""
		self.steam_id = False

		self.pong_stime = 0
		self.ping_lag = 0

		self.loadout = []
		self.loadout_next = []
		self.prefabs = []
		self.prefabs_next = []
		self.loadout_send_default = False

		self.pos_x, self.pos_y, self.pos_z = 0.0, 0.0, 0.0
		self.dir_x, self.dir_y, self.dir_z = 0.0, 0.0, 0.0
		self.vel_x, self.vel_y, self.vel_z = 0.0, 0.0, 0.0
		self.health = 100
		self.curtool = 0x05
		self.curinp = 0x0000

	def disconnect(self, data, from_client=False):
		"""
		Disconnects this client from the server.
		"""

		print "* %s (IP %s) disconnected" % (self.name, "?")
		self.peer.disconnect(data)
		self.alive = False

	@postc("0 <= team <= 3 if registered", lambda r, self, *a, **b : (not self.has_registered) or (self.team >= 0 and self.team <= 3))
	def enter_game(self, team, cls, loadout, name, instant=False):
		"""
		Attempt to make player enter game.
		"""

		# extra sanity
		if team < 0 or team > 3:
			return

		# follow a different path if already registered
		if self.has_registered:
			# check if team or class has changed
			if self.team != team or self.cls != cls:
				old_team = self.team

				# change team/class
				self.loadout = self.loadout_next[:]
				self.prefabs = self.prefabs_next[:]
				self.team = team
				self.cls = cls

				# check if we need to kill this player for respawn
				if old_team == -1 or instant:
					# respawn instantly
					pass # TODO
				else:
					# kill then wait for spawn

					# Why does this happen when moving to spectator?
					# Because it prevents people from respawning on their or the enemy team faster than they should.
					# e.g. ",3,11" without stopping them moving to spectator quickly meaks they can skip the respawn timer.
					# The alternative is to intercept TO non-spec teams rather than FROM.

					pass # TODO
		else:
			# Set fields
			self.loadout = self.loadout_next[:]
			self.prefabs = self.prefabs_next[:]
			self.bcolor = bcolor or [127, 127, 127]
			self.name = name
			self.team = team
			self.cls = cls

			# Send spawn packet
			x, y, z = 256.0, 256.0, 1.0

			print "* %s (IP %s) connected - joined team %i" % (self.name, "?", self.team)

	def decrypt(self, s):
		"""
		Decrypts an XOR'ed packet.
		"""

		# If you get a completely empty steam key, the client is not logged onto Steam.
		# Either that or they just didn't send a key.
		if self.steam_key == "":
			return s

		# If you don't know this algorithm, learn it.
		# Or you will be doomed to repeat it.
		# (It's super-ineffective!)
		rs = ""
		for i in xrange(len(s)):
			rs += chr(ord(s[i]) ^ ord(self.steam_key[i % len(self.steam_key)]))

		return rs
	
	def on_tick(self, dt):
		"""
		EVENT: Called every net tick.
		"""
		if self.player_id == None:
			return

		speed = 0.2
		vmul = 2.0
		self.pos_x += self.dir_x * dt * speed
		self.pos_y += self.dir_y * dt * speed
		self.pos_z += self.dir_z * dt * speed
		self.vel_x  = self.dir_x * speed * vmul
		self.vel_y  = self.dir_y * speed * vmul
		self.vel_z  = self.dir_z * speed * vmul

	def on_event_recv(self, event):
		"""
		EVENT: Called every time a regular ENet event is received.
		"""

		# Ignore really short packets. Because, y'know, we need to read a packet ID. It's kinda necessary.
		if event.packet.dataLength < 2:
			return

		s = str(event.packet.data)

		if s[0] == "\x31":
			# This packet is "compressed" after encryption.
			# Which actually makes the packet bigger.
			# Can someone at Blitz PLEASE leave the crackpipe alone?
			s = lzf.decompress(s[1:])
		else:
			s = s[1:]

		s = self.decrypt(s)
		pid = ord(s[0])
		s = s[1:]
		print "packet", hex(pid), len(s), ''.join('.' if ord(v) < 32 or ord(v) >= 127 else v for v in s), " ".join("%02X" % (ord(v)) for v in s)
		if pid == PKT_STEAM_KEY: 
			# 0x62: Steam Key (used as encraption)
			ticketlen, = struct.unpack("<I", s[:4])
			self.steam_key = s[4:4+ticketlen]
			sdecoded = ""
			for i in xrange(len(self.steam_key)//2):
				sdecoded += chr(int("0x" + self.steam_key[i*2:][:2], 16))
			s = s[4+ticketlen:]

			if len(sdecoded) > 8:
				self.steam_id = struct.unpack("<Q", sdecoded[:8])
				print "Steam key received from %s - Steam ID is %s" % (self, self.steam_id)
			else:
				self.steam_id = None
				print "No steam key from %s - client playing in offline mode" % self

			reactor.push(time.time()+0.2, self.send_info)
		elif pid == PKT_PING_PONG:
			# 0x00: Ping Pong
			# WINE FIX: Use the previous "upper" bytes
			# Say, if you got rid of that "encryption" which totally worked and totally fooled me,
			# this wouldn't be a problem, because that's where the bug is
			if len(s) < 8:
				s += struct.pack("<II", self.ping_ctime, 0)[len(s):]

			self.ping_ctime, = struct.unpack("<I", s[:4])
			self.send(chr(PKT_PING_PONG) + struct.pack("<II", self.ping_ctime, self.server.time))
		elif pid == PKT_PLAYER_INPUT:
			# 0x04: Player Input
			(self.pong_stime, _, self.curtool, dir_x, dir_y, dir_z,
			_, self.curinp, _)= struct.unpack("<IBBHHHBHH", s)
			self.dir_x = fromfixed(dir_x)
			self.dir_y = fromfixed(dir_y)
			self.dir_z = fromfixed(dir_z)
			pass
		elif pid == PKT_SET_LOADOUT:
			# 0x0D: Set Loadout
			# WINE FIX: This just doesn't work at all. Give the player a default once we've found the class.
			if len(s) < 4:
				print "Wine user detected"
				self.loadout_send_default = True
			else:
				# XXX: This code is completely untested.
				_, cls, _, loadout_size = struct.unpack("<BBBB", s[:4])
				s = s[4:]
				self.loadout_next = list(ord(v) for v in s[:loadout_size])
				s = s[loadout_size:]
				if len(s) > 1:
					prefabs_size = ord(s[0])
					s = s[1:]
					self.prefabs_next = []
					for i in xrange(prefabs_size):
						if len(s) == 0:
							break
						v, _, s = s.partition("\x00")
						self.prefabs_next.append(v)
				else:
					self.prefabs_next = []
				s = s[1:]

		elif pid == PKT_ENTER_GAME:
			team, cls, _ = struct.unpack("<BBH", s[:4])
			s = s[4:]
			name, _, s = s.partition("\x00")

			if team >= 0 and team <= 3 and team != 1:
				self.team_next = team
			if cls >= 0x00 and cls <= 0x0C:
				self.cls_next = cls

			# TODO: Check the name for other things we don't want.
			if len(name) <= 1:
				name = "Deuce%i" % self.player_id

			# WINE FIX: We can't get a loadout at all. Now that we know the class, give a default.
			if self.loadout_send_default:
				self.loadout_next = LOADOUT_DEFAULT[cls][:]
				self.prefabs_next = [] # TODO: We need a list of valid prefabs for each class.

			# TODO: Don't let the Commando have the Glide and Jump jetpacks.

			# Move from "next" to "now".
			self.loadout = self.loadout_next[:]
			self.prefabs = self.prefabs_next[:]
			self.name = name
			self.team = team
			self.cls = cls

			# Set a spawn point.
			self.pos_x, self.pos_y, self.pos_z = 255.5, 255.5, 32.5
			self.dir_x, self.dir_y, self.dir_z = -1.0, 0.0, 0.0
			self.vel_x, self.vel_y, self.vel_z = 0.0, 0.0, 0.0

			# Spawn the player.
			s = chr(PKT_SPAWN_PLAYER)
			s += struct.pack("<BBBB", self.player_id, 0, self.cls, self.team)
			s += struct.pack("<HHHHHHH", 0
				, tofixed(self.pos_x), tofixed(self.pos_y), tofixed(self.pos_z)
				, tofixed(self.dir_x), tofixed(self.dir_y), tofixed(self.dir_z)
			)
			s += self.name + "\x00"
			s += chr(len(self.loadout))
			s += "".join(chr(v) for v in self.loadout)
			s += chr(len(self.prefabs))
			s += "\x00".join(self.prefabs) + "\x00"

			self.send(s)

			# Brag about how awesome we are
			# TODO: find the format of system messages - it's packet 0x32, not packet 0x31
			self.send(struct.pack("<BBB", PKT_CHAT_SYSTEM, 0x00, 0x00) + "Welcome to Ace of Spades! This server is powered by Pyckaxe <3" + "\x00\x01\x00\x00")
			self.send(struct.pack("<BBB", PKT_CHAT_SYSTEM, 0x00, 0x00) + "DISCLAIMER: This server is not hosted by Jagex." + "\x00\x01\x00\x00")
			self.send(struct.pack("<BBB", PKT_CHAT_SYSTEM, 0x00, 0x00) + "Your experience is not necessarily 13+." + "\x00\x01\x00\x00")
		
		elif pid == PKT_CHAT and self.player_id != None:
			# 0x31 Chat

			pid, mtyp = struct.unpack("<BB", s[:2])
			msg = s[2:]

			if not msg.endswith("\x00"):
				# Syntax error. Drop packet.
				pass
			elif msg.startswith("/"):
				self.send(struct.pack("<BBB", PKT_CHAT_SYSTEM, 0x00, 0x00) + "Commands aren't implemented yet." + "\x00\x01\x00\x00")
			else:
				# Echo it back.
				# TODO: relay it to everyone
				s = struct.pack("<BBB", PKT_CHAT, self.player_id, mtyp) + msg
				self.send(s)

		elif pid == PKT_MAP_CRC:
			# 0x3C: Map CRC-32 checksum
			# WINE FIX: Lunar Base has a CRC-32 of 0x3C15E1FF.
			if s == "\xFF":
				s = "\xFF\xE1\x15\x3C"

			# Echo back because we are too lazy to send BRAND NEW MAPS WOW.
			self.send(chr(PKT_MAP_CRC) + s, jprefix=0x31)

			# Send the map
			reactor.push(time.time()+0.2, self.send_map)
		
		else:
			#print "Unknown received:", hex(pid), repr(s)
			pass

	def send(self, s, jprefix=0x30, enflags=enet.PACKET_FLAG_RELIABLE):
		"""
		Sends an LZF-compressed packet to this client.
		"""

		print repr(s)

		s = chr(jprefix) + lzf.compress(s)

		self.peer.send(0, enet.Packet(s, enflags))

	def send_info(self, reactor, time_exec, time_current):
		"""
		Sends server info to this client.
		"""

		print "Sending info..."
		chunker = self.server.map.get_chunker()
		chunks = [s for s in chunker.iter()]
		fname = self.server.map.fname
		crc32 = chunker.crc32 & 0xFFFFFFFFL

		# CONSIDERATIONS:
		# - We are just lumping everything together in one go.
		#   Should we gradually generate the map over time,
		#   or just don't worry about the not quite 1 sec lag spike?

		# 0x69: Welcome
		# A sample (v122): 31 01 03 8C 87 07 4B 0E 40 01 E5 D0 F5 AD 7F 80 00 00 54 44 4D 5F 54 49 54 4C 45 00 54 44 4D 5F 44 45 53 43 52 49 50 54 49 4F 4E 00 54 44 4D 5F 49 4E 46 4F 47 52 41 50 48 49 43 5F 54 45 58 54 31 00 54 44 4D 5F 49 4E 46 4F 47 52 41 50 48 49 43 5F 54 45 58 54 32 00 54 44 4D 5F 49 4E 46 4F 47 52 41 50 48 49 43 5F 54 45 58 54 33 00 54 6F 6B 79 6F 20 4E 65 6F 6E 00 54 6F 6B 79 6F 4E 65 6F 6E 00 BE 0B 0D C4 06 EB 69 00 01 00 C0 01 00 01 01 01 00 01 00 01 00 01 40 00 40 00 02 25 26 00 0E 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 01 41 75 73 74 72 61 6C 69 61 20 53 59 32 2D 39 00 02 14 28 37 EE 14 28 37 EF 00 00 00 00 01
		# A sample (v163): 31 69 00 7C 55 81 7A 0E 40 01 CB ED 5E 40 7F 80 00 00 54 44 4D 5F 54 49 54 4C 45 00 54 44 4D 5F 44 45 53 43 52 49 50 54 49 4F 4E 00 54 44 4D 5F 49 4E 46 4F 47 52 41 50 48 49 43 5F 54 45 58 54 31 00 54 44 4D 5F 49 4E 46 4F 47 52 41 50 48 49 43 5F 54 45 58 54 32 00 54 44 4D 5F 49 4E 46 4F 47 52 41 50 48 49 43 5F 54 45 58 54 33 00 4C 6F 6E 64 6F 6E 00 4C 6F 6E 64 6F 6E 00 80 1B 53 23 06 00 EB 69 00 01 00 C0 01 00 01 01 01 00 01 00 01 00 01 40 00 40 00 02 25 26 00 0E 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 00 01 55 53 20 45 61 73 74 20 41 54 32 33 2D 39 00 02 3B 3A 37 EE 28 36 40 EF 00 00 00 00 01 06
		s = chr(PKT_WELCOME)
		s += "\x00\x7C\x55\x81\x7A\x0E\x40\x01"
		s += struct.pack("<BBBB", 1, 0, 0, 127)
		s += struct.pack("<I", 32887)
		s += "TDM_TITLE" + "\x00"
		s += "TDM_DESCRIPTION" + "\x00"
		s += "TDM_INFOGRAPHIC_TEXT1" + "\x00"
		s += "TDM_INFOGRAPHIC_TEXT2" + "\x00"
		s += "TDM_INFOGRAPHIC_TEXT3" + "\x00"
		s += "<3 " + fname + "\x00"
		#s += fname + "\x00"
		s += "LunarBase" + "\x00"

		s += "\x80\x1B\x53\x23"
		s += "\x06" # Game Mode (affects the infographic)
		s += "\x00"
		s += "\xEB\x69"

		# This is too much effort. We'll just go with this trick until we make sense of everything.
		# 00 01 00 C0 01 00 01 01 01 00 01 00 01 00 01 40 00 40 00 02 25 26 00 0E 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 00 01
		s += ''.join(chr(eval("0x" + v)) for v in "00 01 00 C0 01 00 01 01 01 00 01 00 01 00 01 40 00 40 00 02 25 26 00 0E 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 01".split(" "))
		# 55 53 20 45 61 73 74 20 41 54 32 33 2D 39 00
		s += "pyckaxe <3" + "\x00"
		# 02 3B 3A 37 EE 28 36 40 EF 00 00 00 00 01 06
		s += "\x02\x3B\x3A\x37\xEE\x28\x36\x40\xEF"
		# s += "\x02\x14\x28\x37\xEE\x14\x28\x37\xEF"
		s += "\x00\x4F\x4E\x00\x01"
		s += "\x06"

		# This is getting stupid. Let's just drop in a random line I have.
		# Oops, haven't applied decraption yet.
		#s = ''.join(chr(eval("0x" + v)) for v in "69 02 50 DC 2D 68 0E 40 01 E5 D0 F5 AD 78 80 00 00 43 54 46 5F 54 49 54 4C 45 00 43 54 46 5F 44 45 53 43 52 49 50 54 49 4F 4E 00 43 54 46 5F 49 4E 46 4F 47 52 41 50 48 49 43 5F 54 45 58 54 31 00 43 54 46 5F 49 4E 46 4F 47 52 41 50 48 49 43 5F 54 45 58 54 32 00 43 54 46 5F 49 4E 46 4F 47 52 41 50 48 49 43 5F 54 45 58 54 33 00 43 6C 61 73 73 69 63 00 43 6C 61 73 73 69 63 00 70 DC B0 99 08 00 E4 69 01 00 00 C0 01 00 00 01 01 00 01 00 00 01 01 40 00 40 00 02 25 26 00 0E 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 40 00 00 01 41 75 73 74 72 61 6C 69 61 20 53 59 32 2D 32 00 04 55 3C 1E 20 1F 16 0B ED 3B 3A 37 EE 4B 71 9D EF 00 01 00 02 52 55 4C 45 5F 43 54 46 5F 45 4E 41 42 4C 45 5F 49 4E 54 45 4C 5F 41 55 54 4F 5F 52 45 54 55 52 4E 00 4F 46 46 00 52 55 4C 45 5F 43 54 46 5F 45 4E 41 42 4C 45 5F 53 48 4F 4F 54 5F 57 49 54 48 5F 49 4E 54 45 4C 00 4F 4E 00 01 06".split(" "))
		self.send(s, jprefix=0x31)
	
	def send_map(self, reactor, time_exec, time_current):
		"""
		Sends a map to this client.
		"""

		print "Sending map..."
		chunker = self.server.map.get_chunker()
		self.q_chunks = [s for s in chunker.iter()]
		fname = self.server.map.fname
		crc32 = chunker.crc32 & 0xFFFFFFFFL

		# Map
		self.send(struct.pack("<B", PKT_MAP_START), jprefix=0x32)
		self.send_map_chunk(reactor, time_exec, time_current)
	
	def send_map_chunk(self, reactor, time_exec, time_current):
		for i in xrange(10):
			if len(self.q_chunks) == 0:
				return self.send_after_map(reactor, time_exec, time_current)
			else:
				c = self.q_chunks.pop(0)
				self.send(struct.pack("<BBH", PKT_MAP_CHUNK, 100, len(c)) + c, jprefix=0x31)

		reactor.push(time_exec+0.01, self.send_map_chunk)
	
	def send_after_map(self, reactor, time_exec, time_current):
		self.send(struct.pack("<B", PKT_MAP_END), jprefix=0x31)

		print "Map sent! More crap to follow."

		# Game State
		# TDM example (v122): 2C 07 41 6F A3 40 00 DD FB FF 1A 00 13 00 26 80 16 28 4D 06 80 40 80 13 00 22 31 6D 10 00 40 00 C8 06 01
		# blog-1381116239.txt (v163): 2D 06 DF D7 6F 40 00 DC C0 B4 0D 00 33 00 00 00 40 40 40 06 80 26 80 13 00 40 38 34 0D 00 40 00 05 08 01 54 45 41 4D 31 5F 43 4F 4C 4F 52 00 B3 75 2C 00 00 00 00 0C 01 05 54 45 41 4D 32 5F 43 4F 4C 4F 52 00 2C B3 89 00 00 00 00 0C 01 05 01 00 00 04 00 21 00 10 03 FF EE 48 1B 57 00 3C 00 00 00 00 08 80 00 00 40 22 C0 2C 00 0B 00 00 04 00 0F 00 00 00 22 00 19 03 FF 80 40 40 72 00 2E 00 00 00 00 00 00 00 00 C0 3F C0 3F C0 3F 00 00 04 00 00 00 00 00 23 00 10 02 FF 87 3E 4F 21 40 2F 00 00 00 00 08 80 00 00 00 0B 40 1D C0 2C 00 00 04 00 0F 00 00 00 24 00 19 02 FF 40 3E 00 1E 40 2D 00 00 00 00 00 00 00 00 C0 3F C0 3F C0 3F 00 00 04 00 00 00 00 00 00 00 00
		s = chr(PKT_GAME_STATE)
		s += chr(self.player_id)
		s += "\xDF\xD7\x64\x40"
		s += "\x00\xDC\xC0\xB4"
		s += "\x0D\x00\x33\x00"
		s += "\x00\x00\x40\x40"
		s += "\x40\x06\x80\x26"
		s += "\x80\x13\x00\x40"
		s += "\x38\x34\x0D\x00"
		s += "\x40\x00"
		s += chr(252) # Max Score
		s += chr(6) # Game Mode
		s += "\x01"

		# 54 45 41 4D 31 5F 43 4F 4C 4F 52 00 B3 75 2C 00 00 00 00 0C 01 05
		# 54 45 41 4D 32 5F 43 4F 4C 4F 52 00 2C B3 89 00 00 00 00 0C 01 05
		s += "TEAM1_COLOR" + "\x00"
		s += struct.pack("<BBBIB", 0xB3, 0x75, 0x2C, 0, 0x0C)
		s += "\x02\x01\x02" # Rifle Master Race (added rocketeer in just in case it ever works)
		s += "TEAM2_COLOR" + "\x00"
		s += struct.pack("<BBBIB", 0x2C, 0xB3, 0x89, 0, 0x0C)
		s += "\x04\x00\x01\x0C\x03"

		# 01 00 00 04 00 21 00 10 03 FF EE 48 1B 57 00 3C 00 00 00 00 08 80 00 00 40 22 C0 2C 00 0B 00 00 04 00 0F 00 00 00 22 00 19 03 FF 80 40 40 72 00 2E 00 00 00 00 00 00 00 00 C0 3F C0 3F C0 3F 00 00 04 00 00 00 00 00 23 00 10 02 FF 87 3E 4F 21 40 2F 00 00 00 00 08 80 00 00 00 0B 40 1D C0 2C 00 00 04 00 0F 00 00 00 24 00 19 02 FF 40 3E 00 1E 40 2D 00 00 00 00 00 00 00 00 C0 3F C0 3F C0 3F 00 00 04 00 00 00 00 00 00 00 00
		s += "\x01\x00"
		s += "\x00"

		# Entity list
		s += struct.pack("<H", 0) # Length - sending no entities because I'm lazy... well, I'm not up to that bit yet
		
		# List 1
		s += chr(0)
		
		# List 2
		s += chr(0)

		# Some byte
		s += "\x00"

		self.send(s, jprefix=0x31)

		# Mesh File
		self.send(chr(PKT_MESH_FILE) + "Classic.txt" + "\x00")

		return

		# 0x25: I really don't know what this does, and I really hope I don't need to touch it right now
		s = "\x25"
		s += "\x00"*12
		s += "\x18" + "amb_arctic" + "\x00"
		s += "\x01\x00"
		s += "\x1A" + "amb_arctic" + "\x00"
		s += "\x01\x00"
		s += "\x40\x00\x00\x00"
		s += "\x01"

		self.send(s)

		print "Map ready to send!"

