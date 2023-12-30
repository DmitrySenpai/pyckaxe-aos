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
Game mode handling fluff
"""

class GameMode:
	"""
	Base game mode: TDM at its blandest.
	"""
	def __init__(self, server, **kwargs):
		"""
		server is the JagexServer instance you wish to bind this game mode to.
		"""
		self.server = server

	def on_tick(self, stime):
		"""
		Called every net tick.
		"""
		pass

