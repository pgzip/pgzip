from setuptools import setup, find_packages
from pgzip import __version__

with open('README.md') as fh:
    longDesc = fh.read().replace("CompressionBenchmark.png", "https://raw.githubusercontent.com/vinlyx/pgzip/master/CompressionBenchmark.png").replace("DecompressionBenchmark.png", "https://raw.githubusercontent.com/vinlyx/pgzip/master/DecompressionBenchmark.png")

setup(
    name='pgzip',
    version=__version__,
    author='pgzip team',
    author_email='pgzip@thegoldfish.org',

    description='A multi-threading implementation of Python gzip module',
    long_description=longDesc,
    long_description_content_type="text/markdown",
    url='https://github.com/pgzip/pgzip',
    license='MIT',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
    ],
    python_requires=">=3.6"
)
