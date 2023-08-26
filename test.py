# import gzip as pgzip
import time

import pgzip


def _test():
    import os
    import sys

    # Act like gzip; with -d, act like gunzip.
    # The input file is not deleted, however, nor are any other gzip
    # options or features supported.
    args = sys.argv[1:]
    decompress = args and args[0] == "-d"
    if decompress:
        arg = args[1]
    else:
        arg = args[0]
    # if not args:
    #     args = ["-"]
    if decompress:
        tsize = 0
        if arg != "-":
            # outf = arg + ".dcp"
            outf = "/dev/null"
            fh = open(outf, "wb")
            gh = pgzip.open(arg, "rb")
            t0 = time.time()
            # gh.show_index()
            # data = b"AAA"
            chunk_size = 10**7
            while True:
                data = gh.read(chunk_size)
                # data = gh.readline()
                if not data:
                    break
                fh.write(data)
                tsize += len(data)
            # data = gh.readline()
            t1 = time.time()
            fh.close()
            gh.close()
            size = tsize / (1024**2)
            seconds = t1 - t0
            speed = size / seconds
            nsize = os.stat(arg).st_size
            print(
                "Decompressed {:.2f} MB data in {:.2f} S, Speed: {:.2f} MB/s, Rate: {:.2f} %".format(
                    size, seconds, speed, nsize / tsize * 100
                )
            )
    else:
        if arg != "-":
            outf = arg + ".gz"
            fh = open(arg, "rb")
            gh = pgzip.open(outf, "wb", compresslevel=6)
            data = fh.read()
            t0 = time.time()
            gh.write(data)
            gh.close()
            t1 = time.time()
            size = len(data) / (1024**2)
            seconds = t1 - t0
            speed = size / seconds
            nsize = os.stat(outf).st_size
            print(
                "Compressed {:.2f} MB data in {:.2f} S, Speed: {:.2f} MB/s, Rate: {:.2f} %".format(
                    size, seconds, speed, nsize / len(data) * 100
                )
            )


if __name__ == "__main__":
    _test()
