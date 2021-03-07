
import logging
import webcolors
import numpy as np
from PIL import Image

from pyblock.block_colors import block_colors

L = logging.getLogger("pyblock")


class PyMap:
    """
    Holds a complete map for each level and the plotting data.
    """
    def __init__(self, area, output):
        """Initializes the map with the given area coordinates and the output folder.

        Args:
            area (list): 2 dimensional matrix containing the map area
            output (str): output folder
        """ 
        # Set coordinate limits
        self.xmin = area[0][0]
        self.xmax = area[1][0]
        self.zmin = area[0][2]
        self.zmax = area[1][2]

        # Set the output folder
        self.output = output

        # Get total ranges
        self.deltax = self.xmax - self.xmin
        self.deltaz = self.zmax - self.zmin

        # Define empty levels
        self.levels = [PyLevel(y, self.deltax, self.deltaz) for y in range(256)]
        
        # Set of unknown blocks
        self.unknown_blocks = set()

    def set_block(self, x, y, z, block):
        """Sets block for given absolute coordinates.

        Args:
            x,y,z (int): absolute coordinates 
            block (Block): the block at these coordinates
        """
        # Obtain the color from the mapping
        if block.id in block_colors:
            colorname = block_colors[block.id]
        else:
            colorname = 'Red'
            self.unknown_blocks.add(block.id)
        color =  webcolors.name_to_rgb(colorname)
        
        # Set the color at that position
        self.levels[y].set_block_at_coord(x - self.xmin, z - self.zmin, color)
        
    def draw(self):
        """Draws the map.
        """
        L.info("Drawing the map.")
        for y in range(256):
            self.levels[y].draw(self.output)
    
class PyLevel:
    """
    Object to hold the plotting data for a specific y level
    """
    def __init__(self, y, dx, dz):
        """Initializes a level.

        Args:
            y (int): level dimension
            dx, dz (int): Dimension of the plot (in blocks)
        """
        # Level dimension (between 1 and 255)
        self.y = y
        
        # Dimensions of the image
        self.dx = dx
        self.dz = dz
        
        # size of the data array
        self.data = np.zeros((dx, dz, 3), dtype=np.uint8)
        
    def set_block_at_coord(self, x, z, color):
        """Set the color for position x/z.

        Args:
            x,z (int): the coordinates in the image
            color: the color at this point
        """
        if x>0 and x<self.dx and z>0 and z<self.dz:
            # The x coordinate must be mirrored to match reality
            self.data[self.dx - x - 1, z] = color
        
        
    def draw(self, output):
        """Draws and saves a resized image.

        Args:
            output (str): The output folder
        """
        scale = 5
        image = Image.fromarray(self.data)
        newimage = image.resize((scale * self.dx, scale * self.dz), Image.NEAREST)
        newimage.save(f"{output}/level{self.y}.png")
        
        