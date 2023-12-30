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
Constants for the 1.x server
"""

"""
Various constants pertaining to this specific version.
"""
#AOS_VERSION = 168
AOS_VERSION = 163
PLAYERS_MAX_PROTO = 32
CONNECTIONS_MAX = 32
CONNECTIONS_MAX_ENET = CONNECTIONS_MAX + 2
NAME_LEN_MAX = 15 # TODO: get the correct maximum name length... or just drop this field entirely
NET_FPS = 30.0
NET_SPF = 1.0 / NET_FPS

"""
Performance tuning.
"""
MAP_SEND_ROWS = 4
MAP_PACKET_SIZE = 1024

"""
Weapons.
"""
# TODO: find out what these are

"""
Disconnection reasons.

These are fed into the "data" field of a disconnection packet.
Anything out of this range just displays a "Server disconnect" message
as if you were to use DC_GENERIC.
"""
# TODO: find out what the other constants are
(DC_GENERIC, DC_BANNED, DC_KICKED, DC_VERSION, DC_FULL) = xrange(5)

"""
Chat packet types.
"""
(CHAT_ALL, CHAT_TEAM, CHAT_SYSTEM) = xrange(3)

"""
Packets.

See this link for more information: http://aoswiki.rakiru.com/index.php/Ace_of_Spades_Protocol
"""
PKT_STEAM_KEY = 0x62
PKT_PING_PONG = 0x00
PKT_WELCOME = 0x69
PKT_WORLD_UPDATE = 0x02
PKT_PLAYER_INPUT = 0x04
PKT_SET_LOADOUT = 0x0D
PKT_EXISTING_PLAYER = 0x0E
PKT_ENTER_GAME = 0x0F
PKT_SPAWN_PLAYER = 0x1C
PKT_GAME_STATE = 0x2D
PKT_CHAT = 0x31
PKT_CHAT_SYSTEM = 0x32
PKT_MESH_FILE = 0x33
PKT_MAP_START = 0x37
PKT_MAP_CHUNK = 0x39
PKT_MAP_END = 0x3B
PKT_MAP_CRC = 0x3C

"""
Player classes.
"""
CLASS_COMMANDO = 0x00
CLASS_MARKSMAN = 0x01
CLASS_ROCKETEER = 0x02 # It still exists in-game!
CLASS_MINER = 0x03
CLASS_ENGINEER = 0x0C

"""
Loadouts.
"""

# Default loadouts for us Linux users who have to deal with broken code.
# As the first person to get this working, I get to dicate the defaults.
# TODO: There are more loadouts. Do them.

# This order is closest to 0.x.
LOADOUT_DEFAULT_ORDER_0x = {
	CLASS_COMMANDO: [0x02, 0x05, 0x08, 0x0B, 0x0D, 0x17, 0x1E, 0x19, 0x1A, 0x1E],
	CLASS_MARKSMAN: [0x00, 0x05, 0x13, 0x11, 0x14, 0x17, 0x1E, 0x19, 0x1A, 0x1E],
	CLASS_MINER: [0x03, 0x05, 0x09, 0x15, 0x0E, 0x17, 0x1E, 0x19, 0x1A, 0x1E],
	CLASS_ENGINEER: [0x00, 0x05, 0x07, 0x1D, 0x34, 0x17, 0x1E, 0x19, 0x1A, 0x1E],

	CLASS_ROCKETEER: [0x00, 0x05, 0x07, 0x0B, 0x2A, 0x17, 0x1E, 0x19, 0x1A, 0x1E],
}

# This is the default 1.x order.
LOADOUT_DEFAULT_ORDER_1x = {
	CLASS_COMMANDO: [0x05, 0x02, 0x08, 0x0D, 0x0B, 0x17, 0x1E, 0x19, 0x1A, 0x1E],
	CLASS_MARKSMAN: [0x05, 0x00, 0x13, 0x11, 0x14, 0x17, 0x1E, 0x19, 0x1A, 0x1E],
	CLASS_MINER: [0x05, 0x03, 0x09, 0x0E, 0x15, 0x17, 0x1E, 0x19, 0x1A, 0x1E],
	CLASS_ENGINEER: [0x05, 0x00, 0x07, 0x1D, 0x34, 0x17, 0x1E, 0x19, 0x1A, 0x1E],

	CLASS_ROCKETEER: [0x05, 0x00, 0x07, 0x0B, 0x2A, 0x17, 0x1E, 0x19, 0x1A, 0x1E],
}

LOADOUT_DEFAULT = LOADOUT_DEFAULT_ORDER_0x

# This is what each class is allowed by default.
# If you want to change these, be my guest.
LOADOUT_DEFAULT_ALLOWED = {
	CLASS_COMMANDO: [[0x02, 0x01], [0x05], [0x08], [0x0C, 0x0D], [0x0B, 0x20], [0x16], [0x17], [0x1E], [0x19], [0x1A], [0x1E]],
	CLASS_MARKSMAN: [[0x00, 0x01], [0x05], [0x12, 0x13], [0x11], [0x14], [0x16], [0x17], [0x1E], [0x19], [0x1A], [0x1E]],
	CLASS_MINER: [[0x03, 0x01], [0x05], [0x12, 0x13], [0x11], [0x14], [0x16], [0x17], [0x1E], [0x19], [0x1A], [0x1E]],
	CLASS_ENGINEER: [[0x00], [0x05], [0x07], [0x10, 0x1D], [0x34], [0x16], [0x17], [0x1E], [0x19], [0x1A], [0x1E]],

	CLASS_ROCKETEER: [[0x00, 0x02], [0x05], [0x07], [0x0B, 0x10], [0x2A, 0x2B], [0x16], [0x17], [0x1E], [0x19], [0x1A], [0x1E]],
}

# TODO.
PREFAB_DEFAULT_ALLOWED = {
}

"""
Bad names list.
Add to this what you don't want to see in names.
"""
# TODO: check if we CAN use this
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


