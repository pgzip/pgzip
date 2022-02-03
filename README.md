# pgzip

[![Run tests](https://github.com/pgzip/pgzip/actions/workflows/python-tests.yml/badge.svg)](https://github.com/pgzip/pgzip/actions/workflows/python-tests.yml)
[![CodeQL](https://github.com/pgzip/pgzip/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/pgzip/pgzip/actions/workflows/codeql-analysis.yml)

<p align="center">
  <img src="pgzip_logo.png" />
</p>

`pgzip` is a multi-threaded `gzip` implementation for `python` that increases the compression and decompression performance.

Compression and decompression performance gains are made by parallelizing the usage of block indexing within a `gzip` file. Block indexing utilizes gzip's `FEXTRA` feature which records the index of compressed members. `FEXTRA` is defined in the official `gzip` specification starting at version 4.3. Because `FEXTRA` is part of the `gzip` specification, `pgzip` is compatible with regular `gzip` files.

`pgzip` is **~25X** faster for compression and **~7X** faster for decompression when benchmarked on a 24 core machine. Performance is limited only by I/O and the `python` interpreter.

Theoretically, the compression and decompression speed should be linear with the number of cores available. However, I/O and a language's general performance limits the compression and decompression speed in practice.

## Usage and Examples

### CLI
```
❯ python -m pgzip -h
usage: __main__.py [-h] [-o OUTPUT] [-f FILENAME] [-d] [-l {0-9}] [-t THREADS] input

positional arguments:
  input                 Input file or '-' for stdin

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file or '-' for stdout (Default: Input file with 'gz' extension or stdout)
  -f FILENAME, --filename FILENAME
                        Name for the original file when compressing
  -d, --decompress      Decompress instead of compress
  -l {0-9}, --compression-level {0-9}
                        Compression level; 0 = no compression (Default: 9)
  -t THREADS, --threads THREADS
                        Number of threads to use (Default: Determine automatically)
```

### Programatically

Using `pgzip` is the same as using the built-in `gzip` module.

Compressing data and writing it to a file:

```python
import pgzip

s = "a big string..."

# An explanation of parameters:
# `thread=8` - Use 8 threads to compress. `None` or `0` uses all cores (default)
# `blocksize=2*10**8` - Use a compression block size of 200MB
with pgzip.open("test.txt.gz", "wt", thread=8, blocksize=2*10**8) as fw:
    fw.write(s)
```

Decompressing data from a file:

```python
import pgzip

s = "a big string..."

with pgzip.open("test.txt.gz", "rt", thread=8) as fr:
    assert fr.read(len(s)) == s
```



## Performance

### Compression Performance

![Compression Performance](CompressionBenchmark.png)

### Decompression Performance

![Decompression Performance](DecompressionBenchmark.png)

Decompression was benchmarked using an 8.0GB `FASTQ` text file with 48 threads across 24 cores on a machine with Xeon(R) E5-2650 v4 @ 2.20GHz CPUs.

The compressed file used in this benchmark was created with a blocksize of 200MB.

## Warning

`pgzip` only replaces the following methods of `gzip`'s `GzipFile` class:

- `open()`
- `compress()`
- `decompress()`

Other class methods and functionality have not been well tested.

Contributions or improvements is appreciated for methods such as:

- `seek()`
- `tell()`

## History

Created initially by Vincent Li (@vinlyx), this project is a fork of [https://github.com/vinlyx/mgzip](https://github.com/vinlyx/mgzip). We had several bug fixes to implement, but we could not contact them. The `pgzip` team would like to thank Vincent Li (@vinlyx) for their hard work. We hope that they will contact us when they discover this project.
