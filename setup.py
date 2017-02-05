from setuptools import setup, find_packages

version_parts = (0, 7, 2)
version = '.'.join(map(str, version_parts))

setup(
    name='kallikrein',
    description='spec framework',
    version=version,
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    url='https://github.com/tek/kallikrein',
    packages=find_packages(exclude=['unit', 'unit.*']),
    install_requires=[
        'amino>=9.3.0',
        'golgi',
        'hues',
    ],
    entry_points={
        'console_scripts': [
            'klk = kallikrein.run.cli:klk',
        ],
    },
)
