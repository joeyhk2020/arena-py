import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

setuptools.setup(
    name="arena-py",
    version="0.3.0",
    author="Conix Research Center",
    author_email="info@conix.io",
    license="BSD 3-clause \"New\" or \"Revised License\"",
    description="Draw objects and run programs in the ARENA using Python!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arenaxr/ARENA-py",
    packages=setuptools.find_packages(),
    entry_points = {
        'console_scripts': [
            'arena=arena.__main__:cli',
            'arena-py-permissions=arena.scripts.arena_py_permissions:main',
            'arena-py-pub=arena.scripts.arena_py_pub:main',
            'arena-py-signout=arena.scripts.arena_py_signout:main',
            'arena-py-sub=arena.scripts.arena_py_sub:main',
            'arena-py-token=arena.scripts.arena_py_token:main'
        ],
    },
    install_requires=[
        "aiohttp>=3.7.4",
        "paho-mqtt~=1.6.1",
        "requests~=2.28.1",
        "webcolors~=1.3",
        "google_auth_oauthlib~=0.5.2",
        "google-auth~=1.35.0",
        "PyJWT~=2.4.0",
        "numpy>=1.22",
        "scipy>=1.5.4"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
