#!/usr/bin/env python3
from setuptools import setup
from sys import platform

# Load README.md as long description
repository = path.abspath(path.dirname(__file__))
with open(path.join(repository, 'README.md'), encoding='utf-8') as f:
    readme = f.read()

setup(
    name='Carton',
    version='0.0.0',

    description='An extensive and extensible dotfiles manager',
    long_description=readme,

    author='Neil Cecchini',
    author_email='stranger.neil@gmail.com',

    license='MIT',

    keywords='dotfiles automation',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    ],

    packages=['carton'],
    python_requires='>=3',

    # NOTE: We only depend on `pyobjc` if we're building for macOS
    install_requires=['pyobjc'] if platform == 'darwin' else [],

    entry_points={
        'console_scripts': [
            'carton=carton:main'
        ]
    }
)
