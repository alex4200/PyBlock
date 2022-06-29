#!/usr/bin/env python3
"""Module to plot maps for every level."""
__author__ = "Alexander Dietz"
__license__ = "MIT"
# pylint: disable=C0103,W1202,E1120,R0913,R0914,E0401,R0902,W1203

import os
import json
import logging
import numpy as np
from PIL import Image

import pyblock
from .tools import indexsplit, MIN_SECTION, MAX_SECTION

L = logging.getLogger("pyblock")


class PyMap:
    """
    Holds a complete map for each level and the plotting data.
    """

    def __init__(self, area: list, output: str, colormap_file: str):
        """Initializes the map with the given area coordinates and the output folder.

        Args:
            area: 2-dimensional matrix containing the map area in absolute coordinates (x/z)
            output: output folder
            colormap: Name of the colormap json file
        """
        # Set coordinate limits
        self.xmin = area[0][0]
        self.xmax = area[1][0]
        self.zmin = area[0][1]
        self.zmax = area[1][1]

        # Set the output folder
        self.output = output

        # Get total ranges
        self.deltax = self.xmax - self.xmin
        self.deltaz = self.zmax - self.zmin

        # Define empty levels
        self.levels = {
            y: PyLevel(y, self.deltax, self.deltaz)
            for y in range(16 * MIN_SECTION, 16 * (MAX_SECTION + 1))
        }

        # Set of unknown blocks
        self.unknown_blocks = set()

        # Load default color map
        path = os.path.dirname(os.path.realpath(__file__))
        with open(path + "/color_map.json", encoding="UTF-8") as json_file:
            self.colormap = json.load(json_file)

        # Load user color map (if specified)
        self.usermap = None
        if colormap_file:
            with open(colormap_file, encoding="UTF-8") as json_file:
                self.usermap = json.load(json_file)

    def set_blocks_for_map(self, region: pyblock.Region, list_chunks: list):
        """Add blocks to a Map.

        Args:
            region: The region to parse
            list_chunk: List of chunk coordinates
        """
        n = len(list_chunks)
        for index, chunk_coord in enumerate(list_chunks):
            L.debug(
                f"Analyzing chunk {index}/{n} at chunk-coordinates "
                f"{region.x_chunk + chunk_coord[0]}/{region.z_chunk + chunk_coord[1]}"
            )

            # Absolute coordinates of the chunk
            base_x = 512 * region.x + 16 * chunk_coord[0]
            base_z = 512 * region.z + 16 * chunk_coord[1]
            chunk = region.get_chunk(chunk_coord)

            for ylevel in range(MIN_SECTION, MAX_SECTION):
                section = chunk.get_section(ylevel)
                for idx, block in enumerate(section.blocks):
                    x, y, z = indexsplit(idx)
                    cx = x + base_x
                    cy = y + 16 * ylevel
                    cz = z + base_z
                    self.set_block(cx, cy, cz, block.id[10:])

    def set_block(self, x: int, y: int, z: int, block: str):
        """Sets block for given absolute coordinates.

        Args:
            x,y,z: absolute coordinates
            block: the block at these coordinates
        """
        # Obtain the color of a block from the default or usermap
        color = None
        if self.usermap:
            if block in self.usermap:
                color = self.usermap[block]
        if not color:
            if block in self.colormap:
                color = self.colormap[block]
        if not color:
            color = [255, 255, 255]
            self.unknown_blocks.add(block)

        # Set the color at that position
        self.levels[y].set_block_at_coord(x - self.xmin, z - self.zmin, color)

    def draw(self):
        """Draws the map."""
        L.info(f"Drawing the map to {self.output}.")
        for level in self.levels.values():
            level.draw(self.output)


class PyLevel:
    """
    Object to hold the plotting data for a specific y level
    """

    def __init__(self, y: int, dx: int, dz: int):
        """Initializes a level.

        Args:
            y: level dimension
            dx, dz: Dimension of the plot (in blocks)
        """
        # Level dimension
        self.y = y

        # Dimensions of the image
        self.dx = dx
        self.dz = dz

        # size of the data array
        self.data = np.zeros((dx, dz, 3), dtype=np.uint8)

    def set_block_at_coord(self, x: int, z: int, color: tuple):
        """Set the color for position x/z.

        Args:
            x,z: the coordinates in the image
            color: the color at this point
        """
        if 0 <= x < self.dx and 0 <= z < self.dz:
            # The x coordinate must be mirrored to match reality
            self.data[self.dx - x - 1, z] = color

    def draw(self, output: str):
        """Draws and saves a resized image.

        Args:
            output: The name of the image output folder
        """
        # Create the image itself
        scale = 5
        image = Image.fromarray(self.data)
        newimage = image.resize((scale * self.dx, scale * self.dz), Image.NEAREST)

        # Create the filename
        img_number = self.y - 16 * MIN_SECTION
        filename = f"{output}/plot{img_number:03d}_level{self.y}.png"

        # Save the image to the file
        newimage.save(filename)
