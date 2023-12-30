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
Ace of Spades 0.76 server constants
"""

"""
Various constants pertaining to this specific version.
"""
AOS_VERSION = 4
PLAYERS_MAX_PROTO = 32
CONNECTIONS_MAX = 32
CONNECTIONS_MAX_ENET = CONNECTIONS_MAX + 2
NAME_LEN_MAX = 15

"""
Performance tuning.
"""
MAP_SEND_ROWS = 4
MAP_PACKET_SIZE = 1024

"""
Weapons.
"""
(WPN_RIFLE, WPN_SMG, WPN_SHOTGUN) = xrange(3)

"""
Disconnection reasons.

These are fed into the "data" field of a disconnection packet.
Anything out of this range just displays a "Server disconnect" message
as if you were to use DC_GENERIC.
"""
(DC_GENERIC, DC_BANNED, DC_KICKED, DC_VERSION, DC_FULL) = xrange(5)

"""
Chat packet types.
"""
(CHAT_ALL, CHAT_TEAM, CHAT_SYSTEM) = xrange(3)

"""
Packets.

See this link for more information: http://aoswiki.rakiru.com/index.php/Ace_of_Spades_Protocol
"""
PKT_POSITION = 0
PKT_ORIENTATION = 1
PKT_WORLD_UPDATE = 2
PKT_EXISTING_PLAYER = 9
PKT_CREATE_PLAYER = 12
PKT_STATE_DATA = 15
PKT_CHAT = 17
PKT_MAP_START = 18
PKT_MAP_CHUNK = 19

"""
Bad names list.
Add to this what you don't want to see in names.
"""
BAD_NAMES = [
	# English
	"fuck", "shit", "cunt", "bitch", " nigg", "faggot",
	" mother", " mom ", " mum ", "mutha", "motha", "muther", "momma", "mumma", "moma", "muma",

	# Portuguese
	"puta", "puto", "porra",
	" madr",

	# German
	"fick",
	"mutter", "mudder", "mutta", "mudda",

	# Names used to mislead players
	"admin", "server", "[*]",

	# Names commonly used by griefers
	"minecraft", "creeper", "herobrine", "killer",
]

