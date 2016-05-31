from setuptools import setup
import sshuttle

setup(
    name='sshuttle',
    version=sshuttle.__version__,
    description='sshuttle is an ssh vehicle for your environment',
    packages=['sshuttle'],
    entry_points={
        'console_scripts': [
            'sshuttle = sshuttle.cli:cli',
        ]
    }
)
