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
Team-related classes
"""

class Team:
	"""
	"""
	def __init__(self, server, name, index, bcolor, **kwargs):
		"""
		server is the JagexServer instance you wish to bind this team to.
		name is the name you wish to give this team.
		index is the index of this team. 0x02 and 0x03 are the player teams, 0x00 is spectator, and 0x01 is neutral.
		"""
		self.server = server
		self.name = name
		self.index = index
		self.bcolor = bcolor[:]

