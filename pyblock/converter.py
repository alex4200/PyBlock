#!/usr/bin/env python3
"""
This module contains utility functions for coordinate conversions.
"""

import math

# Size of a region (in units of blocks)
REGION_SIZE = 512

# Size of a chunk (in units of blocks)
CHUNK_SIZE = 16


def dist(a0, a1, b0, b1):
    """Returns the Eucleadean distance between two points in 2D."""
    da = a1-a0
    db = b1-b0
    return math.sqrt(da*da + db*db)

def block_to_chunk(x, z):
    """Returns chunk coordinates given block coordinates."""
    chunk_x = int(math.floor(x / CHUNK_SIZE))
    chunk_z = int(math.floor(z / CHUNK_SIZE))
    return (chunk_x, chunk_z)

def chunk_to_block(x, z):
    """Returns min/max block coordinates given chunk coordinates."""
    min_x = CHUNK_SIZE * x
    min_z = CHUNK_SIZE * z
    max_x = CHUNK_SIZE * (x + 1) -1
    max_z = CHUNK_SIZE * (z + 1) -1
    return ((min_x, max_x), (min_z, max_z))

def region_to_block(x,z):
    """Returns min/max block coordinates given region coordinates."""
    min_x = REGION_SIZE * x
    min_z = REGION_SIZE * z
    max_x = REGION_SIZE * (x + 1) -1
    max_z = REGION_SIZE * (z + 1) -1
    return ((min_x, max_x), (min_z, max_z))

def chunk_to_region(x,z):
    """Returns region coordinates given chunk coordinates."""
    region_x = int(math.floor(x * CHUNK_SIZE / REGION_SIZE))
    region_z = int(math.floor(z * CHUNK_SIZE / REGION_SIZE))
    return (region_x, region_z)

def block_to_region(x,z):
    """Returns region coordinates given block coordinates."""
    region_x = int(math.floor(x / REGION_SIZE))
    region_z = int(math.floor(z / REGION_SIZE))
    return (region_x, region_z)
