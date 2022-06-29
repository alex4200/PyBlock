

from pyblock import tools

def test_block_to_region():
	assert tools.block_to_region(0,0) == (0,0)
	assert tools.block_to_region(0,511) == (0,0)
	assert tools.block_to_region(0,512) == (0,1)
	assert tools.block_to_region(511,0) == (0,0)
	assert tools.block_to_region(512,0) == (1,0)
	assert tools.block_to_region(-1,-1) == (-1,-1)

def test_block_to_chunk():
	assert tools.block_to_chunk(0,0) == (0,0)
	assert tools.block_to_chunk(511,511) == (31,31)
	assert tools.block_to_chunk(15,0) == (0,0)
	assert tools.block_to_chunk(0,15) == (0,0)
	assert tools.block_to_chunk(0,16) == (0,1)
	assert tools.block_to_chunk(16,0) == (1,0)

def test_block_to_ylevel():
	assert tools.block_to_ylevel(0) == 0
	assert tools.block_to_ylevel(-1) == -1
	assert tools.block_to_ylevel(-64) == -4
	assert tools.block_to_ylevel(100) == 6

def test_block_to_id_index():
	assert tools.block_to_id_index(0,0,0) == (((0,0), (0,0), 0), 0)
	assert tools.block_to_id_index(712, 70, 612) == (((1,1), (12,6), 4), 1608)

