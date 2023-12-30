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
Rudimentary implementation of the Ace of Spades 0.76 protocol
"""

from pyckaxe.constants import *
from pyckaxe.util import *
from pyckaxe.classic.constants import *
import pyckaxe.server
import pyckaxe.classic.connection
import pyckaxe.classic.map

CSParent = pyckaxe.server.Server
class ClassicServer(CSParent):
	"""
	Server to handle the Ace of Spades 0.76 gameplay and protocol.
	"""
	@override
	def __init__(self, port):
		self.connections = [None for i in xrange(CONNECTIONS_MAX)]
		self.map = None
		self.map_queued = None
		pyckaxe.server.Server.__init__(self, port, 1)
		self.host.compress_with_range_coder()
	
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
				conn = self.connections[player_id] = defexcept(Exception, None)(lambda : pyckaxe.classic.connection.ClassicConnection(self, event.peer, player_id))()
				return DC_GENERIC if conn == None else None
		
		return DC_FULL
	
	def load_map(self, fname):
		"""
		Loads an AoS map from a file.
		"""

		m = pyckaxe.classic.map.Map()
		if m.load(fname):
			self.map_queued = m
			if self.map == None:
				self.map, self.map_queued = self.map_queued, None
			return True
		else:
			return False
	
	@override
	def on_connect(self, event):
		# Peer must have the correct version.
		print(event.data)
		#if event.data != AOS_VERSION:
		#	return DC_VERSION

		# Peer must not already be in the pool.
		# If the peer is in the pool, we need to disconnect the peer,
		# as this is probably a deliberate low-level exploit.
		#if self.has_peer(event.peer):
		#	return DC_KICKED

		return self.client_accept(event)

