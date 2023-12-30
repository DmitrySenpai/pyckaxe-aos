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
Base server for handling events 'n' stuff
"""

import enet
import time
from pyckaxe.constants import *
from pyckaxe.util import *
from pyckaxe.reactor import reactor

class Server:
	"""
	Base class for the Pyckaxe server which all servers are expected to subclass.
	"""
	def __init__(self, port, channels):
		"""
		port indicates the UDP port which this server is meant to use.
		channels indicates how many ENet channels to use.
		"""
		self.addr = enet.Address(None, port)
		self.host = enet.Host(self.addr, channels)
	
	def on_idle(self, time_current, time_remain):
		"""
		EVENT: At the start of every idle period, this is called.

		You can use this as an opportunity to spawn more tasks in the reactor.
		"""
		pass

	def on_event_recv(self, event):
		"""
		EVENT: Called every time a regular ENet event is received.
		"""
		pass

	def on_disconnect(self, event):
		"""
		EVENT: Called every time a client disconnects.
		"""
		pass

	def on_connect(self, event):
		"""
		EVENT: Called every time a client connects.

		Return None to accept the connection.
		Return an integer to disconnect.

		This will NOT send an on_disconnect message.
		"""

		return 0

	def update_network(self, reactor, time_exec, time_current):
		"""
		Polls the ENet host and calls on_packet_recv and stuff repeatedly.
		"""
		while True:
			event = self.host.service(1)

			if event.type == enet.EVENT_TYPE_NONE:
				break
			elif event.type == enet.EVENT_TYPE_RECEIVE:
				self.on_event_recv(event)
			elif event.type == enet.EVENT_TYPE_CONNECT:
				r = self.on_connect(event)
				if r != None:
					event.peer.disconnect(r)
			elif event.type == enet.EVENT_TYPE_DISCONNECT:
				self.on_disconnect(event)
			else:
				raise Exception("Type %s is not a valid ENet event type" % event.type)
		reactor.push(time_exec + 1.0/30.0, self.update_network)

	@postc("run_forever_and_ever must run forever and ever", lambda *a, **b : False)
	def run_forever_and_ever(self):
		reactor.push(time.time(), self.update_network)
		while True:
			time_delta, time_spent = reactor.update()
			if time_delta == None:
				print "Reactor ran out of tasks!"
				break
			time_remain = time_delta - time_spent
			self.on_idle(time.time(), time_remain)
			if time_remain > 0.0:
				#print time_remain
				time.sleep(time_remain)

