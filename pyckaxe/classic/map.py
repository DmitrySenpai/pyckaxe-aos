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
Map data for Ace of Spades
"""

from pyckaxe.constants import *
from pyckaxe.util import *
from pyckaxe.classic.constants import *
import struct
import zlib

def filter_1x_light(s):
	"""
	Changes the light level field of a series of block cells to 0x7F.
	"""

	# Interlace.
	l = [s[i::4] for i in xrange(4)]
	
	# Replace the 4th component.
	l[3] = "\x7F" * len(l[3])

	# Deinterlace.
	return ''.join(''.join(q) for q in zip(*((c for c in s) for s in l)))

class Map:
	"""
	Class for an Ace of Spades map.

	Always call .load(fname) if loading from a file
	"""
	def __init__(self):
		self.ready = False
		self.fname = None
		self.g = None
	
	class MapSerialiser:
		"""
		Class for progressively serialising a map.
		"""
		def __init__(self, data):
			# Deep copy the map data.
			self.g = map(lambda l : l[:], data)

		def iter(self):
			"""
			Iterator for collecting data from this map.
			"""
			for i in xrange(0, 512, MAP_SEND_ROWS):
				s = ""
				for j in xrange(MAP_SEND_ROWS):
					l = self.g[i+j]
					s += ''.join(l)

				yield s
	
	class MapPacker:
		"""
		Class for packing a map into a zlib stream.
		"""
		def __init__(self, data):
			self.serialiser = Map.MapSerialiser(data)
			self.crc32 = zlib.crc32("")

		def iter(self):
			comp = zlib.compressobj()
			for s in self.serialiser.iter():
				self.crc32 = zlib.crc32(s, self.crc32)
				yield comp.compress(s)

			yield comp.flush()
	
	class MapChunker:
		"""
		Class for spitting out a bunch of chunks for sending to the client.
		"""
		def __init__(self, data):
			self.packer = Map.MapPacker(data)
			self.crc32 = zlib.crc32("")

		def iter(self):
			s = ""
			for ins in self.packer.iter():
				self.crc32 = self.packer.crc32
				s += ins
				while len(s) >= MAP_PACKET_SIZE:
					yield s[:MAP_PACKET_SIZE]
					s = s[MAP_PACKET_SIZE:]
			
			yield s
	
	@defexcept(Exception, False)
	def load(self, fname):
		# TODO: catch exceptions
		"""
		Loads an Ace of Spades map from a file. 1.x maps will be converted.

		Returns True if it worked.
		Returns False if it didn't.
		"""

		highest_point = 255
		lowest_point = 63

		# Open the file.
		print "Loading map %s..." % repr(fname)
		fp = open(fname, "rb")

		# Split it into vertical entries.
		self.g = []
		for y in xrange(512):
			l = []
			for x in xrange(512):
				s = ""
				while True:
					ns = fp.read(4)

					cand_lowest = max(ord(ns[2]), ord(ns[1]))
					if cand_lowest > lowest_point:
						lowest_point = cand_lowest

					if ord(ns[1]) < highest_point:
						highest_point = ord(ns[1])

					if ord(ns[0]) == 0:
						finals = ord(ns[2]) - ord(ns[1]) + 1
						s += ns + fp.read(4*finals)
						break
					else:
						s += ns + fp.read((ord(ns[0])-1)*4)

				l.append(s)
			
			self.g.append(l)

		# Close our file.
		fp.close()

		# Check if we need to convert it.
		if lowest_point != 63:
			print "Converting 1.x map to 0.x..."

			# Check if we CAN convert it.
			if lowest_point - highest_point > 63:
				print "Cannot convert 1.x map - map is too high!"
				print "Lowest point:", lowest_point
				print "Highest point:", highest_point
				print "Height:", lowest_point - highest_point + 1
				return False

			map_shift = 63 - lowest_point

			for y in xrange(512):
				l = self.g[y]
				for x in xrange(512):
					sb = l[x]
					s = ""
					while True:
						ns, sb = sb[:4], sb[4:]

						ns = ns[0] + chr(ord(ns[1]) + map_shift) + chr(ord(ns[2]) + map_shift) + chr(max(0, ord(ns[3]) + map_shift))
						if ord(ns[0]) == 0:
							# 1.x water needs to be given explicitly to prevent AoS from crashing
							if ns[0] == "\x00" and ord(ns[1]) == 63:
								ns = "\x00\x3F\x3F" + ns[3] + struct.pack("<BBBB", 255, 128, 0, 127)
							finals = ord(ns[2]) - ord(ns[1]) + 1
							k = 4*finals
							rs, sb = sb[:k], sb[k:]
							s += ns + filter_1x_light(rs)
							break
						else:
							k = (ord(ns[0])-1)*4
							rs, sb = sb[:k], sb[k:]
							s += ns + filter_1x_light(rs)

					l[x] = s
				if (y+1)%32 == 0:
					print "%3.2f%% complete" % (float(100*(y+1))/512.0)

		print "Map loaded!"

		# Report that everything is fine and dandy.
		# TODO: use the right path separator for the right OS
		self.fname = '.'.join(fname.replace("\\","/").split("/")[-1].split(".")[:-1])
		self.ready = True
		return True
	
	def get_chunker(self):
		"""
		Gets a MapChunker object which can be iterated over.
		"""
		return self.MapChunker(self.g)

