Unofficial Python API for Dropcam cameras.

Please note that this API could break if Dropcam updates their service.

Usage
-----

Basic usage ::

    >>> from dropcam import Dropcam
    >>> d = Dropcam(os.getenv("DROPCAM_USERNAME"), 
                    os.getenv("DROPCAM_PASSWORD"))
    >>> for i, cam in enumerate(d.cameras()):
    ...     cam.save_image("camera.%d.jpg" % i)

Installation
------------

Using easy install ::

    $ pip install dropcam

Or from source ::

    $ git clone https://github.com/rsgalloway/dropcam.git
    $ cd dropcam
    $ python setup.py install
