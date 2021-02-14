# Main Code for editing blocks

import logging
from pathlib import Path

from .block import Block
from .region import Region
from . import converter as conv


L = logging.getLogger("pyblock")


class MCEditor:

	__slots__ = ('path','blocks_map')
	def __init__(self, path):
		"""Initialize the editor with the path to the world.

		Args:
			path (str): Path to the world folder.
		"""
		# Set the world path
		self.path = Path(path) / "region"

		# Dict for the blocks to be set
		self.blocks_map = {}

	def set_block(self, block, x, y, z):
		"""
        Records position and block to be modified.
        
        Args:
        	block (Block): Minecraft Block
        	x, y, z (int): World Coordinates
        """
        # Get the region and the chunk coordinates where to set the block
		region_coord, chunk_coord, block_coord = conv.block_to_region_chunk(x,z)

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

	def done(self):
		"""
		Modify the world with the recorded blocks.
		"""

		# Loop over all regions that are affected
		for region_coord, chunks in self.blocks_map.items():
			region = Region(self.path, *region_coord)
			region.update_chunks(chunks)

