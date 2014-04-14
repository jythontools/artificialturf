import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages


setup(
    name = "greenlet",  # note that we fake the name here! this is artififical after all...
    version = "0.1",    # but what version should it be?
    packages = find_packages()
)
