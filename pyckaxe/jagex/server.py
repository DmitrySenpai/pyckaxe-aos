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
Rudimentary implementation of the Ace of Spades 1.x protocol (or a version of it anyway)
"""

from pyckaxe.constants import *
from pyckaxe.util import *
from pyckaxe.jagex.constants import *
from pyckaxe.reactor import reactor
import pyckaxe.jagex.lzf as lzf
import pyckaxe.server
import pyckaxe.jagex.connection
import pyckaxe.jagex.gamemode
import pyckaxe.jagex.map
import pyckaxe.jagex.team
import struct
import time

JSParent = pyckaxe.server.Server
class JagexServer(JSParent):
	"""
	Server to handle the Ace of Spades 1.x gameplay and protocol.
	"""
	@override
	def __init__(self, port):
		self.connections = [None for i in xrange(CONNECTIONS_MAX)]
		self.teams = [
			pyckaxe.jagex.team.Team(self, "SPECTATOR", 0x00, [0xFF, 0xFF, 0xFF]),
			pyckaxe.jagex.team.Team(self, "NEUTRAL", 0x01, [0x80, 0x80, 0x80]),
			pyckaxe.jagex.team.Team(self, "TEAM1_COLOR", 0x02, [0xB3, 0x75, 0x2C]),
			pyckaxe.jagex.team.Team(self, "TEAM2_COLOR", 0x03, [0x2C, 0xB3, 0x89]),
		]
		self.gamemode = pyckaxe.jagex.gamemode.GameMode(self)
		self.map = None
		self.map_queued = None
		self.time = 0
		pyckaxe.server.Server.__init__(self, port, 1)
		self.host.compress_with_range_coder()
	
	@override
	def run_forever_and_ever(self, *args, **kwargs):
		reactor.push(time.time() + NET_SPF, self.on_tick)
		pyckaxe.server.Server.run_forever_and_ever(self, *args, **kwargs)

	def has_peer(self, peer):
		"""
		Returns to see whether we are handling this ENet peer or not.
		"""

		# The filter() step is necessary to make pyenet's horribly incomplete comparators behave
		return self.get_peer_connection(peer) != None

	def get_peer_connection(self, peer):
		"""
		Gets a connection class given a peer, or None if it could not be found.
		"""

		for conn in self.connections:
			if conn != None and conn.peer == peer:
				return conn

		return None
	
	def on_tick(self, reactor, time_exec, time_current):
		"""
		Called every net tick.
		"""
		self.time += 1
		#print "Tick"

		for c in self.connections:
			if c != None:
				c.on_tick(dt=NET_SPF)

		self.gamemode.on_tick(self.time)

		# 0x02: World Update
		if (self.time % 2) == 0:
			l_player = []
			for c in self.connections:
				if c != None and c.player_id != None:
					s = ""
					s += struct.pack("<B", c.player_id)
					s += struct.pack("<fff", c.pos_x, c.pos_y, c.pos_z)
					s += struct.pack("<fff", c.dir_x, c.dir_y, c.dir_z)
					s += struct.pack("<fff", c.vel_x, c.vel_y, c.vel_z)
					# TODO: calculate ping
					s += struct.pack("<HI", 5, c.pong_stime)
					s += struct.pack("<H", c.health)
					s += struct.pack("<H", c.curinp)
					s += struct.pack("<BB", 0x00, c.curtool)
					s += struct.pack("<B", 0xFF)
					s += struct.pack("<HI", tofixed(100.0), 0)
					l_player.append(s)

			s = chr(PKT_WORLD_UPDATE)
			s += struct.pack("<I", self.time)
			s += struct.pack("<H", len(l_player)) # Number of players
			s += "".join(l_player)
			s += struct.pack("<H", 0) # Number of ?
			s += struct.pack("<H", 0) # Number of ?

			#print "upd", len(self.connections)
			for c in self.connections:
				if c != None:
					c.send(s)

		# Loop around
		reactor.push(time_exec + NET_SPF, self.on_tick)

	@override
	def on_event_recv(self, event):
		conn = self.get_peer_connection(event.peer)
		if conn == None:
			return

		return conn.on_event_recv(event)

	@prec("peer must not be accepted twice", lambda self, event, *a, **b : not self.has_peer(event.peer))
	@postc("connections must not exceed limit", lambda r, self, event, *a, **b : len(self.connections) <= PLAYERS_MAX_PROTO)
	def client_accept(self, event):
		"""
		Attempts to accept a client to the server.
		"""

		for player_id in xrange(PLAYERS_MAX_PROTO):
			if self.connections[player_id] == None:
				conn = self.connections[player_id] = defexcept(Exception, None)(lambda : pyckaxe.jagex.connection.JagexConnection(self, event.peer, player_id))()
				return DC_GENERIC if conn == None else None

		return DC_FULL

	def load_map(self, fname):
		"""
		Loads an AoS map from a file.
		"""

		m = pyckaxe.jagex.map.Map()
		if m.load(fname):
			self.map_queued = m
			if self.map == None:
				self.map, self.map_queued = self.map_queued, None
			return True
		else:
			return False

	@override
	def on_connect(self, event):
		print "Peer attempting to connect"
		# Peer must have the correct version.
		print(event.data)
		if event.data != AOS_VERSION:
			print "Invalid version"
			return DC_VERSION

		# Peer must not already be in the pool.
		# If the peer is in the pool, we need to disconnect the peer,
		# as this is probably a deliberate low-level exploit.
		if self.has_peer(event.peer):
			print "Peer already in pool"
			return DC_KICKED

		print "Accepting peer"
		return self.client_accept(event)

