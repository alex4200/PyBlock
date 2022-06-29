from setuptools import setup, find_packages
import os
import re

setup(
    name='PyBlock',
    version=open('VERSION.txt').read().strip(),
    author='Alexander Dietz',
    author_email='alexander.dietz17@gmail.com',
    packages=find_packages(where='.', exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    package_data={}, 
    license=open('LICENSE.txt').read().strip(),
    description='Tool to analyze block in minecraft maps.',
    long_description="Tool to analyze block in minecraft maps.",
    include_package_data=True,
    install_requires=[
        'click',
        'nbt',
        'frozendict',
        'webcolors',
        'pillow',
        'numpy'
    ],
    entry_points={
        'console_scripts': [
            'pyblock=pyblock.mcmain:cli'
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: MIT',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ],
)
