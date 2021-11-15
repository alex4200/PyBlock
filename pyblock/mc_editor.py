# Main Code for editing blocks

import glob
import logging
from pathlib import Path

from .block import Block
from .region import Region
from .tools import block_to_region_chunk
from . import converter as conv
from .maze import Maze


L = logging.getLogger("pyblock")


class MCEditor:

    __slots__ = ("path", "blocks_map", "local_chunks")

    def __init__(self, path):
        """Initialize the editor with the path to the world.

        Args:
                path (str): Path to the world folder.
        """
        # Set the world path
        self.path = Path(path) / "region"

        # Dict for the blocks to be set
        self.blocks_map = {}

        # Dict to hold local chunk data for faster 'get_block'
        self.local_chunks = {}

    def set_verbosity(self, verbose):
        """Sets the verbosity level. Possible values are 0, 1 or 2
        """
        level = (logging.WARNING, logging.INFO, logging.DEBUG)[min(verbose, 2)]
        L.setLevel(level)

    def set_block(self, block, x, y, z):
        """
        Records position and block to be modified.

        Args:
                block (Block): Minecraft Block
                x, y, z (int): World Coordinates
        """
        # Get the region and the chunk coordinates where to set the block
        region_coord, chunk_coord, block_coord = conv.block_to_region_chunk(x, z)

        # Create the location to change (block and coordinates inside the chunk)
        loc = (block, block_coord[0], y, block_coord[1])

        # Fill the location into the blocks-map
        if region_coord in self.blocks_map:
            if chunk_coord in self.blocks_map[region_coord]:
                self.blocks_map[region_coord][chunk_coord].append(loc)
            else:
                self.blocks_map[region_coord][chunk_coord] = [loc]
        else:
            self.blocks_map[region_coord] = {chunk_coord: [loc]}

    def get_block(self, x, y, z):
        """Returns the block at the given absolute coordinates.
        """
        # Get the region coordinates and the relative chunk and block coordinates
        region_coord, chunk_coord, block_coord = block_to_region_chunk(x, z)

        # Check if the chunk is already in the local cache
        chunk_id = (*region_coord, *chunk_coord)
        if chunk_id in self.local_chunks:
            chunk = self.local_chunks[chunk_id]
        else:
            region = Region(self.path, *region_coord)
            chunk = region.get_chunk(*chunk_coord)
            self.local_chunks[chunk_id] = chunk

        coords = block_coord[0], y, block_coord[1]
        return chunk.get_block(*coords)

    def place_piece(
        self, x1, y1, z1, block_floor, block_fill, block_ceil, height=4, mag=1
    ):
        """Places an element of the maze.

        Args:
            x1 (int): x coordinate
            y1 (int): y coordinate
            z1 (int): z coordinate
            block_floor: minecraft block for the floor
            block_fill: minecraft block to fill
            block_ceil: minecraft block for the ceiling
            height (int): The height of the walls
            mag (int): Magnifier of the maze. 1 means 1:1 size, 2 means all walls, ways
                       are double size etc.
        """
        for dx in range(mag):
            for dz in range(mag):
                x = x1 + dx
                z = z1 + dz
                self.set_block(block_floor, x, y1, z)
                for y in range(y1, y1 + height):
                    self.set_block(block_fill, x, y + 1, z)
                self.set_block(block_ceil, x, y1 + height + 1, z)

    def create_maze(self, maze, coord, blocks, height=4, mag=1):
        """Creates and places a maze with given width and height.
        start_coord is the starting coorinates (x,y,z) and
        blocks is a list of the three blocks for the floow, the wall and the ceiling.

        Args:
            size (int, int): Size of the maze in x/z direction
            coord (int, int, int): Start coordinates of the maze
            blocks (string, string, string): Names for the blocks for floor, wall and ceiling
            height (int): Height of the inside of the maze (default: 4)
            mag (int): Magnifier number of the maze (thickness of path/walls)
        """
        # Get the maze as a simple 0/1 matrix
        matrix = maze.get_matrix()

        # Define the blocks
        block_floor = Block("minecraft", blocks[0])
        block_wall = Block("minecraft", blocks[1])
        block_ceil = Block("minecraft", blocks[2])
        block_air = Block("minecraft", "air")

        # Get the coordinates
        x0 = coord[0]
        y0 = coord[1]
        z0 = coord[2]

        # Place the walls, floor and ceiling
        for row, lines in enumerate(matrix):
            for col, block in enumerate(lines):
                x = x0 + mag * row
                z = z0 + mag * col

                if block:
                    self.place_piece(
                        x, y0, z, block_floor, block_wall, block_ceil, mag=mag
                    )
                else:
                    self.place_piece(
                        x, y0, z, block_floor, block_air, block_ceil, mag=mag
                    )

    def _read_map_file(self, map_file):
        """Returns a block dict from the given filename."""
        m = {}
        with open(map_file) as filein:
            for line in filein.readlines():
                t = line.strip().split()
                m[t[0]] = t[1]
        return m

    def from_map(self, path_file, coord, direction="y", repetition=1):
        """Reads a basic template from files and builds it at the given coordinates
        repetition times in the specified direction.

        Args:
            path_file (string): Path to the files(s)
            coord (int,int,int): Starting coordinates
            direction (string): Direction in which the template is repeated
            repetition (int): Number of repetitions
        """
        # Read the block map and find the template files.
        block_map = self._read_map_file(path_file + ".txt")
        tmp_files = glob.glob(path_file + "_*")

        # Get basic coordinates.
        x0, y0, z0 = coord

        # Loop over the repetition.
        for rep in range(repetition):

            y = y0 + rep * len(tmp_files)
            for level in range(len(tmp_files)):
                tmp_file = f"{path_file}_{level:03d}.txt"

                with open(tmp_file) as template:
                    for dx, line in enumerate(template.readlines()):
                        for dz, b in enumerate(line.strip()):
                            block = Block("minecraft", block_map[b])
                            self.set_block(block, x0 + dx, y + level, z0 + dz)

    def done(self):
        """
        Modify the world with the recorded blocks.
        """

        # Loop over all regions that are affected
        for region_coord, chunks in self.blocks_map.items():
            L.info(
                f"Modifying {len(chunks)} chunks in region {region_coord[0]}/{region_coord[1]}/"
            )
            region = Region(self.path, *region_coord)
            update_chunks = region.update_chunks(chunks)
            region.write(update_chunks)
