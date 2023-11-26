from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

setup(
    name='ClientPython',
    version='0.1',
    packages=[''],
    package_dir={'': 'src'},
    install_requires=['pygame', 'python-socketio[client]', '[json]'],
    url='',
    license='',
    author='David Stevic',
    author_email='',
    description=''
)
