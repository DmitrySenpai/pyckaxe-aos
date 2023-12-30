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
Useful functions and decorators and whatnot.
"""

from pyckaxe.constants import *
import traceback

def copydec(f, g):
	"""
	Copies name and docstring from f to g and returns g.
	"""

	g.func_name = f.func_name
	g.func_doc = f.func_doc
	return g

def override(f):
	"""
	DECORATOR: Indicates that this is a function override.
	"""

	# This decorator does nothing yet.
	# You can make it do something if you want.

	return f

def abstract(f):
	"""
	DECORATOR: Indicates that this function must be overridden.
	"""
	
	def _f1(*a, **b):
		raise Exception("Abstract function " + str(f.func_name) + " needs an override!")
	
	return copydec(_f1, f)

def safetycheck_dec(f):
	"""
	DECORATOR: Masks out a decorator when Pyckaxe is not doing safety checks.

	Note, if your decorator takes parameters, use safetycheck_dec_param instead.
	"""

	if SAFETY_CHECKS:
		return f
	else:
		return copydec(f, lambda g : g)

def safetycheck_dec_param(f):
	"""
	DECORATOR: Masks out a parameter-taking decorator when Pyckaxe is not doing safety checks.

	Note, if your decorator does not take parameters, use safetycheck_dec instead.
	"""

	if SAFETY_CHECKS:
		return f
	else:
		return copydec(f, lambda *a, **b : lambda g : copydec(f, g))

@safetycheck_dec_param
def prec(rule, g):
	"""
	DECORATOR: Adds a precondition to a function.

	rule is a string indicating the name of the rule.
	g is a function which takes the function's arguments as parameters and returns either:
	- True if the assertion succeeded, or
	- False if the assertion failed.
	"""
	def _f1(f):
		def _f2(*args, **kwargs):
			assert g(*args, **kwargs), "precondition failed: " + str(rule)
			return f(*args, **kwargs)

		return copydec(f, _f2)

	return _f1

@safetycheck_dec_param
def postc(rule, g):
	"""
	DECORATOR: Adds a postcondition to a function.

	rule is a string indicating the name of the rule.
	g is a function which takes the return value (perhaps as a tuple) and then the function's arguments as parameters and returns either:
	- True if the assertion succeeded, or
	- False if the assertion failed.
	"""
	def _f1(f):
		def _f2(*args, **kwargs):
			r = f(*args, **kwargs)
			assert g(r, *args, **kwargs), "postcondition failed: " + str(rule)
			return r

		return copydec(f, _f2)

	return _f1

def defexcept(e, r, silent=False):
	"""
	DECORATOR: On a specific exception, spits out a stack trace and returns the default value.
	"""

	def _f1(f):
		def _f2(*a, **b):
			# with help from: http://stackoverflow.com/questions/4564559/get-exception-description-and-stack-trace-which-caused-an-exception-all-as-a-st
			try:
				return f(*a, **b)
			except e, d:
				if not silent:
					print "Exception in function call to %s:" % repr(f.func_name)
					print ("\t" + traceback.format_exc().replace("\n", "\n\t"))
				return r

		return copydec(f, _f2)
	
	return _f1

def tofixed(v):
	"""
	1.x: Convert a Float into a Fixed.
	"""
	v *= 64
	v += 0.5
	v = int(v)
	mag = abs(v)
	if mag > 0x7FFF:
		mag = 0x7FFF
	sgn = 0x8000 if v < 0 else 0x0000

	return mag | sgn

def fromfixed(v):
	"""
	1.x: Convert a Fixed into a Float.
	"""
	sgn = -1 if (v & 0x8000) != 0 else 1
	mag = v & 0x7FFF
	mag = float(mag)/64.0

	return mag * sgn

"""
Test cases.
"""
@prec("cat must only say meow or purr", lambda s : s in ("meow", "purr"))
def test_cat_say(s):
	"""
	Make a cat say a cat-like thing.
	"""
	print "Cat: " + str(s)

"""
Run test cases.
"""
if __name__ == "__main__":
	test_cat_say("meow")
	test_cat_say("purr")
	test_cat_say("i love you")

