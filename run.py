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

from pyckaxe.constants import *
import pyckaxe.jagex.server

import sys

PORT = 32888

if __name__ == "__main__":
	server = pyckaxe.jagex.server.JagexServer(PORT)
	server.load_map(sys.argv[1])
	print "TEST: Iterating map data..."
	chunker = server.map.get_chunker()
	chunks = [s for s in chunker.iter()]
	print "Done! name = %s, CRC32 = %08X, chunks = %i, size = %i" % (
		repr(server.map.fname),
		chunker.crc32 & 0xFFFFFFFFL,
		len(chunks), len(''.join(chunks)))
	print "Running server now!", PORT
	server.run_forever_and_ever()

