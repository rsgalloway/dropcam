Unofficial Python API for Dropcam cameras.

Usage
-----

Basic usage ::

    >>> from dropcam import Dropcam
    >>> d = Dropcam(username, password)
    >>> c = d.cameras()[0]
    >>> c.save_image("image.jpg")

Installation
------------

Using easy install ::

    $ easy_install dropcam

Or from source ::

    $ git clone https://github.com/rsgalloway/dropcam.git
    $ cd dropcam
    $ python setup.py install
