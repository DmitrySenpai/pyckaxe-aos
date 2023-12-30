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
LZF compression functions
"""

def decompress(s):
	"""
	Decompress a string that was compressed using the LZF algorithm.
	"""

	# Decompression instructions:
	#
	# %sssddddd
	#
	# If s == 0, the next d+1 bytes are to be copied verbatim.
	# Otherwise:
	#   If s == 7, read the next byte, and add that to s.
	#   Shift d left by 8 (i.e. multiply it by 256), read the next byte, and add that to d.
	#   Add 2 to s, and 1 to d.
	#   Do LZ77 with s as our size and d as our "distance" from the point just past the last character in our output.

	i = 0
	rs = ""
	while i < len(s):
		sd = ord(s[i])
		size = sd >> 5
		dist = sd  & 0x1F
		i += 1

		if size == 0:
			rs += s[i:i+dist+1]
			i += dist+1
		else:
			if size == 7:
				size += ord(s[i])
				i += 1
			dist = (dist<<8) + ord(s[i])
			i += 1

			# We can't use a slice copy here.
			for _ in xrange(size+2):
				rs += rs[-dist]
	
	return rs

def compress_nop(s):
	"""
	Compress a string using the LZF algorithm.

	This version does not compress data at all. Instead, it expects ENet's PPM compressor to do all the compression for us.
	"""

	base_s = s

	rs = ""
	while len(s) > 32:
		rs += "\x1F" + s[:32]
		s = s[32:]
	
	rs += chr(len(s)-1) + s

	assert base_s == decompress(rs)
	return rs

compress = compress_nop

