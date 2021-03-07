#!/usr/bin/env python3
"""
Tools for mcblock.
"""
__author__ = "Alexander Dietz"
__license__ = "MIT"
# pylint: disable=C0103


import math

# Size of a region (in units of blocks)
REGION_SIZE = 512

# Size of a chunk (in units of blocks)
CHUNK_SIZE = 16

# Number of chunks in a region (one dimension)
CHUNKS_REGION = 32

def chunk_to_block(x, z):
    """Returns min/max block coordinates given chunk coordinates.

	Args:
		x,z (int): Chunk coordinates
    """
    min_x = CHUNK_SIZE * x
    min_z = CHUNK_SIZE * z
    max_x = CHUNK_SIZE * (x + 1) -1
    max_z = CHUNK_SIZE * (z + 1) -1
    return ((min_x, max_x), (min_z, max_z))

def chunk_to_region(x, z):
    """Returns region coordinates given chunk coordinates.

	Args:
		x,z (int): Chunk coordinates
    """
    region_x = int(math.floor(x * CHUNK_SIZE / REGION_SIZE))
    region_z = int(math.floor(z * CHUNK_SIZE / REGION_SIZE))
    return (region_x, region_z)

def block_to_region(x, z):
    """Returns region coordinates given block coordinates.

	Args:
		x,z (int): Block coordinates
    """
    return (x // REGION_SIZE, z // REGION_SIZE)

def region_to_block(x, z):
    """Returns min/max block coordinates given region coordinates.
	
	Args:
		x,z (int): Region coordinates.
    """
    min_x = REGION_SIZE * x
    min_z = REGION_SIZE * z
    max_x = REGION_SIZE * (x + 1) -1
    max_z = REGION_SIZE * (z + 1) -1
    return ((min_x, max_x), (min_z, max_z))

def block_to_chunk(x, z):
    """Returns chunk coordinates given block coordinates.

	Args:
		x,z (int): Block coordinates
	"""
    return (x // CHUNK_SIZE, z // CHUNK_SIZE)

def block_to_region_chunk(x, z):
    """Returns region coordinates and relative chunk coordinates for the given coordinates.

	Args:
		x,z (int): Block coordinates
	"""
    region = block_to_region(x, z)
    chunk = block_to_chunk(x % REGION_SIZE, z % REGION_SIZE)
    block = (x % CHUNK_SIZE, z % CHUNK_SIZE)

    return region, chunk, block


def abs_chunk_to_region_chunk(x, z):
	"""Returns region coordinates and relative chunk coordinates 
	for the given absolute chunk coordinates.

	Args:
		x,z (int): Absolute chunk coordinates
	"""
	region = (x//CHUNKS_REGION, z//CHUNKS_REGION)
	chunk = (x%CHUNKS_REGION, z%CHUNKS_REGION)
	return region, chunk


def combine_dicts(dict1, dict2):
	"""Returns a merged counter dictionary.

	Args:
		dict1, dict2: The dictionaries to be merged.
	"""
	d = dict1.copy()
	for key, value in dict2.items():
		if key in d:
			d[key] += value
		else:
			d[key] = value
	return d
