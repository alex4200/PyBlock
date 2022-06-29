#!/usr/bin/env python3
"""
Tools for mcblock.
"""
__author__ = "Alexander Dietz"
__license__ = "MIT"
# pylint: disable=C0103,W1202,E1120,R0913,R0914,E0401,W1203,R1732,W1514,R0912,R0903,R0902,R0911,W1201

import os
import math
from pathlib import Path
from typing import Tuple

import logging

L = logging.getLogger("pyblock")


# Size of a region (in units of blocks)
REGION_SIZE = 512

# Size of a chunk (in units of blocks)
CHUNK_SIZE = 16

# Number of chunks in a region (one dimension)
CHUNKS_REGION = 32

# Minimum and Maximum section level
MIN_SECTION = -4
MAX_SECTION = 19

Y_SECTION_RANGE = {
    "nether": [0,8],
    "overworld": [-4, 19]
}

MIN_Y = CHUNK_SIZE * MIN_SECTION
MAX_Y = CHUNK_SIZE * MAX_SECTION


def get_world_path(world: str, dimension="overworld") -> str:
    """Returns the path to the world, either from an environment variable
    or from a command line argument.

    Args:
        world: Optional path to the world to be used.
        dimension: The dimension to use (overworld, nether)
    """
    if dimension == "nether":
        dim_path = "DIM-1/region"
    else:
        dim_path = "region"

    if world:
        return Path(world) / dim_path
    if "MINECRAFTWORLD" in os.environ:
        return Path(os.environ["MINECRAFTWORLD"]) / dim_path
    raise ValueError("Path to world must be defined. Or set MINECRAFTWORLD.")


def indexsplit(n: int) -> list:
    """Splits a 3-digit hex number into their 3 int value.
    Extracts x,y,z value from integer from 0...4096
    """
    x = n & 15
    n >>= 4
    z = n & 15
    n >>= 4
    y = n & 15
    return x, y, z


def block_index(xs:int, ys:int, zs:int) -> int:
    """Returns the index for the section relative coordinates

    Args:
    xs, ys, zs: Section relative coordinates (0..15)
    """
    #print(xs, ys, zs)
    return ys * 256 + zs * 16 + xs


def block_to_region(x:int, z:int) -> list:
    """Returns region coordinates given block coordinates.

    Args:
        x,z: Block coordinates
    """
    return (x // REGION_SIZE, z // REGION_SIZE)


def block_to_chunk(xr: int, zr: int) -> list:
    """Returns chunk coordinates given block coordinates within the region.

    Args:
        xr,zr: Region relative coordinates (0-511)
    """
    return (xr // CHUNK_SIZE, zr // CHUNK_SIZE)


def block_to_ylevel(y: int) -> int:
    """Returns the y level of the section given the absolute y coordinate.

    Args:
        y: Absolute y coodinate
    """
    return y // CHUNK_SIZE


def block_to_id_index(x: int, y: int, z: int) -> Tuple:
    """Returns the ID of the section and the index of the block location for the section.

    Args:
        x, y, z: Absolute block coordinates
    """
    region = block_to_region(x, z)
    chunk = block_to_chunk(x % REGION_SIZE, z % REGION_SIZE)
    ylevel = block_to_ylevel(y)
    index = block_index(x % CHUNK_SIZE, y % CHUNK_SIZE, z % CHUNK_SIZE)
    return region, chunk, ylevel, index


def get_chunk_area(x: int, z: int, dx: int, dz: int) -> Tuple[dict, list, list]:
    """Returns a dict of the regions and the chunks in the specified area.

    Args:
        x: x coordinate of the start point.
        z: z coordinate of the start point.
        dx: size in x direction.
        dz: size in z direction.

    Returns:
        dict: Dictionary containing the source chunks
        int, int: Chunk-rounded source coordinates
        int, int: Chunk-rounded size to be copied
    """
    # Calculate the minimum and maximum chunks for the edges
    chunk_x_min = block_to_chunk(x, z)[0]
    chunk_x_max = block_to_chunk(x + dx, z)[0]
    chunk_z_min = block_to_chunk(x, z)[1]
    chunk_z_max = block_to_chunk(x, z + dz)[1]
    L.debug(
        f"Absolute chunk range: {chunk_x_min}/{chunk_z_min} to {chunk_x_max}/{chunk_z_max}"
    )

    xmin = chunk_x_min * CHUNK_SIZE
    zmin = chunk_z_min * CHUNK_SIZE
    xmax = (chunk_x_max + 1) * CHUNK_SIZE
    zmax = (chunk_z_max + 1) * CHUNK_SIZE
    L.debug(
        f"Absolute block-range for the chunks to read: {xmin}/{zmin} - {xmax}/{zmax}"
    )

    number_chunks = 0
    regions = {}
    for chunk_x in range(chunk_x_min, chunk_x_max + 1):
        for chunk_z in range(chunk_z_min, chunk_z_max + 1):
            chunk = (chunk_x, chunk_z)
            rel_chunk = (chunk_x % 32, chunk_z % 32)
            number_chunks += 1

            reg = chunk_to_region(*chunk)
            if reg in regions:
                regions[reg].append(rel_chunk)
            else:
                regions[reg] = [rel_chunk]

    # Now we have the regions to be analyzed
    L.info(f"Analyzing {len(regions.keys())} regions and {number_chunks} chunks in total")
    return (regions, (xmin, zmin), (xmax - xmin, zmax - zmin))


def get_regions(region: list, coords: list, radius: int) -> dict:
    """Returns a dictionary containing all related regions (key)
    and the list of relative chunks (values). Used for "list" and "find".

    Args:
        region: region to use (x/z coordinates)
        coords: absolute coordinates of the center point
        radius: radius around the center point
    """
    if region:
        regions = {(region[0], region[1]): "all"}
    else:
        regions, _, _ = get_chunk_area(
            coords[0] - radius, coords[1] - radius, 2 * radius, 2 * radius
        )

    return regions


def get_area(region: list, coords: list, radius: int) -> list:
    """Returns the area in absolute coordinates that is searched for "plot".
    Either coordinates and radius are defined, or the region.

    Args:
        region: region to use (x/z coordinates)
        coords: absolute coordinates of the center point
        radius: radius around the center point

    Returns:
        int, int: area
    """
    # Define the search area
    if region:
        area = None
    else:
        coord_min = [c - radius for c in coords]
        coord_max = [c + radius for c in coords]
        area = (coord_min, coord_max)
    L.debug(f"Search area for 'plot': {area}")
    return area

def chunk_to_region(x: int, z: int) -> list:
    """Returns region coordinates given chunk coordinates.

    Args:
        x,z: Chunk coordinates
    """
    region_x = int(math.floor(x * CHUNK_SIZE / REGION_SIZE))
    region_z = int(math.floor(z * CHUNK_SIZE / REGION_SIZE))
    return (region_x, region_z)
