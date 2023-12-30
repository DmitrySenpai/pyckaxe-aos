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
Connection to an Ace of Spades 0.76 server
"""

from pyckaxe.constants import *
from pyckaxe.util import *
from pyckaxe.classic.constants import *
from pyckaxe.reactor import reactor
import enet
import struct
import time

class ClassicConnection:
	"""
	Necessary state for an Ace of Spades 0.76 connection.
	To avoid OO-fuelled redundancy, this also holds the player state.
	"""
	def __init__(self, server, peer, player_id, **kwargs):
		"""
		server is the ClassicServer instance you wish to bind this connection to.
		peer is the ENet peer this connection pertains to.
		"""
		self.server = server
		self.peer = peer
		self.player_id = player_id

		self.team = -2
		self.weapon = WPN_RIFLE
		self.bcolor = [127, 127, 127]
		self.name = "<unnamed>"

		self.has_registered = False
		self.in_game = False

		self.alive = True

		reactor.push(time.time()+0.5, self.send_map)
	
	def disconnect(self, data, from_client=False):
		"""
		Disconnects this client from the server.
		"""

		print "* %s (IP %s) disconnected" % (self.name, "?")
		self.peer.disconnect(data)
		self.alive = False
	
	@postc("-1 <= team <= 1 if registered", lambda r, self, *a, **b : (not self.has_registered) or (self.team >= -1 and self.team <= 1))
	@postc("0 <= weapon < 3 if registered", lambda r, self, *a, **b : (not self.has_registered) or (self.weapon >= 0 and self.weapon < 3))
	def enter_game(self, team, weapon, bcolor, name, instant=False):
		"""
		Attempt to make player enter game.
		"""

		# extra sanity
		if team < -1 or team > 1:
			return
		if weapon < 0 or weapon >= 3:
			return
		
		# follow a different path if already registered
		if self.has_registered:
			# check if team or weapon has changed
			if self.team != team or self.weapon != weapon:
				old_team = self.team

				# change team/weapon
				self.team = team
				self.weapon = weapon

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
			self.team = team
			self.weapon = weapon
			self.bcolor = bcolor or [127, 127, 127]
			self.name = name

			#self.peer.send(0, enet.Packet(struct.pack("<B", PKT_WORLD_UPDATE), enet.PACKET_FLAG_RELIABLE))

			# Send position
			x, y, z = 256.0, 256.0, 1.0
			# Also send a position packet because this protocol sucks
			self.peer.send(0, enet.Packet(struct.pack("<BBbfff", PKT_CREATE_PLAYER, self.weapon, self.team, x, y, z) + self.name + "\x00", enet.PACKET_FLAG_RELIABLE))
			self.peer.send(0, enet.Packet(struct.pack("<Bfff", PKT_POSITION, x, y, z), enet.PACKET_FLAG_RELIABLE))
			
			print "* %s (IP %s) connected - joined team %i" % (self.name, "?", self.team)

			# Brag about how awesome we are
			# FIXME: this should be somewhere else
			self.peer.send(0, enet.Packet(struct.pack("<BBB", PKT_CHAT, 0, CHAT_SYSTEM) + "Welcome to Ace of Spades! This server is powered by Pyckaxe <3" + "\x00"))

	def on_event_recv(self, event):
		"""
		EVENT: Called every time a regular ENet event is received.
		"""

		# Ignore zero-length packets. Because, y'know, we need to read a packet ID. It's kinda necessary.
		if event.packet.dataLength < 1:
			return

		# Let's get that packet ID.
		s = str(event.packet.data)
		packet_id, s = ord(s[0]), s[1:]
		
		# And now let's discriminate.
		if packet_id == PKT_EXISTING_PLAYER and len(s) >= 11:
			_, team, weapon, _, _, b, g, r = struct.unpack("<BbBBIBBB", s[:11])
			name = s[11:]
			name = name.replace("\x00", "")

			# Some values must be clamped.
			if team < -1 or team > 1:
				team = -1
			if weapon < 0 or weapon > 2:
				weapon = 0

			# There are some names we have to forbid.
			if name.replace(" ","") == "":
				name = "Deuce"
			if len(filter(lambda c : ord(c) < 32 or ord(c) > 126, name)) > 0:
				name = "Deuce"
			if len(filter(lambda badname : badname.lower() in name.lower(), BAD_NAMES)) > 0:
				name = "Deuce"

			# There are other names we have to filter.
			if len(filter(lambda c : c.islower(), name)) > 0:
				name = name.lower()

			# And of course there are traditions we must uphold.
			if name == "Deuce":
				name += str(self.player_id)

			# We must truncate names which are too long (instead of relying on the client to do ANY sanitisation).
			if len(name) > NAME_LEN_MAX:
				name = name[:NAME_LEN_MAX]

			self.enter_game(team, weapon, [b, g, r], name)
		else:
			print "packet", packet_id, len(s)

	def send_map(self, reactor, time_exec, time_current):
		"""
		Sends map data to this client.
		"""
		print "Sending map..."
		chunker = self.server.map.get_chunker()
		chunks = [s for s in chunker.iter()]
		fname = self.server.map.fname
		crc32 = chunker.crc32 & 0xFFFFFFFFL

		# CONSIDERATIONS:
		# - We are just lumping everything together in one go.
		#   Should we gradually generate the map over time,
		#   or just don't worry about the not quite 1 sec lag spike?
		# - We are using the non-checksummed packet for now.

		#self.peer.send(0, enet.Packet(struct.pack("<BI", PKT_MAP_START, crc32) + fname + "\x00", enet.PACKET_FLAG_RELIABLE))

		self.peer.send(0, enet.Packet(struct.pack("<B", PKT_MAP_START), enet.PACKET_FLAG_RELIABLE))
		for c in chunks:
			self.peer.send(0, enet.Packet(struct.pack("<B", PKT_MAP_CHUNK) + c, enet.PACKET_FLAG_RELIABLE))

		# Let's send the state data here, too
		# TODO: It would be a Good Thing to move the packet writing to Somewhere Else.
		s = ""
		s += struct.pack("<BB", PKT_STATE_DATA, self.player_id)
		s += struct.pack("<BBB", 255, 0, 170)
		s += struct.pack("<BBB", 255, 0, 0)
		s += struct.pack("<BBB", 0, 255, 0)
		s += "Blue" + "\x00"*6
		s += "Green" + "\x00"*5
		s += struct.pack("<B", 0)

		# CTF mode
		s += struct.pack("<BBB", 0, 0, 10)
		s += struct.pack("<B", 0)

		# TODO: these thingies need to not be static
		s += struct.pack("<fff", 64, 256, 32)
		s += struct.pack("<fff", 512-64, 256, 32)
		s += struct.pack("<fff", 32, 256, 32)
		s += struct.pack("<fff", 512-32, 256, 32)

		self.peer.send(0, enet.Packet(s, enet.PACKET_FLAG_RELIABLE))

		print "Map ready to send!"

