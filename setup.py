import io
import os

from setuptools import find_packages, setup
from nuwe_cimiss import __version__

DESCRIPTION = "A python API for CMADaaS MUSIC."

here = os.path.abspath(os.path.dirname(__file__))

try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

setup(
    name="nuwe-cimiss-python",
    version=__version__,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Perilla Roc",
    author_email="perillaroc@gmail.com",
    python_requires='>=3.6.0',
    url="https://github.com/perillaroc/nuwe-cimiss-python",
    # package=find_packages(exclude=[
    #     "tests",
    #     "*.tests",
    #     "*.tests.*",
    #     "tests.*",
    #     "music-sdk-python-*",
    # ]),
    py_modules=["nuwe_cimiss"],
    install_requires=[
        "requests",
        "numpy",
        "pandas",
        "pyyaml",
        "protobuf",
    ],
    extras_requires={
        "example": ["click"]
    },
    include_package_data=True,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
