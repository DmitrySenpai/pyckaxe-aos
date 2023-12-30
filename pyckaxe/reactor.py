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
"""

import heapq
import time
from pyckaxe.constants import *
from pyckaxe.util import *

class Reactor:
	"""
	Magical time-keeping scheduler class type thing.
	"""
	def __init__(self):
		self.events = []

	def push(self, time_exec, f):
		"""
		Adds an event to be called at time time_exec.

		Function f takes parameters (reactor, time_exec, time_current).
		"""
		heapq.heappush(self.events, (time_exec, f))

	@postc("return value must either be True, None, or non-negative", lambda r, self, time_current : r == True or r == None or r >= 0.0)
	def poll(self, time_current):
		# Do we have anything in the queue?
		if not self.events:
			return None
		
		# Peek at it.
		(time_exec, f) = self.events[0]

		# Should it happen yet?
		if time_exec > time_current:
			return time_exec - time_current

		# Pop it and run it.
		heapq.heappop(self.events)
		defexcept(Exception, None)(f)(self, time_exec, time_current)
		return True
	
	def update(self):
		time_current = time.time()
		while True:
			r = self.poll(time_current)
			if r == True:
				continue

			return r, time.time() - time_current

reactor = Reactor()

poll = reactor.poll
push = reactor.push
update = reactor.update


