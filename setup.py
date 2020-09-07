import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("LICENSE", "r") as fh:
    LICENSE = fh.read()

setuptools.setup(
    name='labequipment',
    version='0.1',
    license=LICENSE,
    packages=setuptools.find_packages(
        exclude=('tests', 'docs')
    ),
    url='https://github.com/MikeSmithLabTeam/labvision',
    install_requires=[
        'pyserial',
        'numpy',
        'picoscope'
    ],
    test_suite='nose.collector',
    tests_require=['nose']
)
