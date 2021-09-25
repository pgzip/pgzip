"""This module provide a simple replacement of Python internal gzip module
to provide a multiprocessing solution for gzip compression/decompression.

License: MIT LICENSE
Copyright (c) 2019 Vincent Li

"""

import os, time
import builtins
import struct
import zlib
import io
from gzip import GzipFile, write32u, _GzipReader, _PaddedFile, READ, WRITE, FEXTRA, FNAME, FCOMMENT, FHCRC
from multiprocessing.dummy import Pool

__version__ = "0.3.0"

SID = b'IG' # Subfield ID of indexed gzip file

def open(filename, mode="rb", compresslevel=9,
         encoding=None, errors=None, newline=None,
         thread=None, blocksize=10**8):
    """Open a gzip-compressed file in binary or text mode.

    The filename argument can be an actual filename (a str or bytes object), or
    an existing file object to read from or write to.

    The mode argument can be "r", "rb", "w", "wb", "x", "xb", "a" or "ab" for
    binary mode, or "rt", "wt", "xt" or "at" for text mode. The default mode is
    "rb", and the default compresslevel is 9.

    For binary mode, this function is equivalent to the GzipFile constructor:
    GzipFile(filename, mode, compresslevel). In this case, the encoding, errors
    and newline arguments must not be provided.

    For text mode, a GzipFile object is created, and wrapped in an
    io.TextIOWrapper instance with the specified encoding, error handling
    behavior, and line ending(s).

    """
    if "t" in mode:
        if "b" in mode:
            raise ValueError("Invalid mode: %r" % (mode,))
    else:
        if encoding is not None:
            raise ValueError("Argument 'encoding' not supported in binary mode")
        if errors is not None:
            raise ValueError("Argument 'errors' not supported in binary mode")
        if newline is not None:
            raise ValueError("Argument 'newline' not supported in binary mode")

    gz_mode = mode.replace("t", "")
    if isinstance(filename, (str, bytes)):
        binary_file = PgzipFile(filename, gz_mode, compresslevel, thread=thread, blocksize=blocksize)
    elif hasattr(filename, "read") or hasattr(filename, "write"):
        binary_file = PgzipFile(None, gz_mode, compresslevel, filename, thread=thread, blocksize=blocksize)
    else:
        raise TypeError("filename must be a str or bytes object, or a file")

    if "t" in mode:
        return io.TextIOWrapper(binary_file, encoding, errors, newline)
    else:
        return binary_file

def compress(data, compresslevel=9, thread=None, blocksize=10**8):
    """Compress data in one shot and return the compressed string.
    Optional argument is the compression level, in range of 0-9.
    """
    buf = io.BytesIO()
    with PgzipFile(fileobj=buf, mode='wb', compresslevel=compresslevel,
                       thread=thread, blocksize=blocksize) as f:
        f.write(data)
    return buf.getvalue()

def decompress(data, thread=None, blocksize=10**8):
    """Decompress a gzip compressed string in one shot.
    Return the decompressed string.
    """
    with PgzipFile(fileobj=io.BytesIO(data), thread=thread,
                       blocksize=blocksize) as f:
        return f.read()

def padded_file_seek(self, off, whence=0):
    """
        Provide a whence of seek method in gzip
        to allow seek to the end of file.
        * FIXME: This method may have some problem
         is stream mode since it is unable to seek
         to the end of stream object.
    """
    self._read = None
    self._buffer = None
    return self.file.seek(off, whence)
_PaddedFile.seek = padded_file_seek # override the seek method to provide whence parameter

class PgzipFile(GzipFile):
    """ docstring of PgzipFile """

    def __init__(self, filename=None, mode=None,
                 compresslevel=9, fileobj=None, mtime=None,
                 thread=None, blocksize=10**8):
        """Constructor for the GzipFile class.

        At least one of fileobj and filename must be given a
        non-trivial value.

        The new class instance is based on fileobj, which can be a regular
        file, an io.BytesIO object, or any other object which simulates a file.
        It defaults to None, in which case filename is opened to provide
        a file object.

        When fileobj is not None, the filename argument is only used to be
        included in the gzip file header, which may include the original
        filename of the uncompressed file.  It defaults to the filename of
        fileobj, if discernible; otherwise, it defaults to the empty string,
        and in this case the original filename is not included in the header.

        The mode argument can be any of 'r', 'rb', 'a', 'ab', 'w', 'wb', 'x', or
        'xb' depending on whether the file will be read or written.  The default
        is the mode of fileobj if discernible; otherwise, the default is 'rb'.
        A mode of 'r' is equivalent to one of 'rb', and similarly for 'w' and
        'wb', 'a' and 'ab', and 'x' and 'xb'.

        The compresslevel argument is an integer from 0 to 9 controlling the
        level of compression; 1 is fastest and produces the least compression,
        and 9 is slowest and produces the most compression. 0 is no compression
        at all. The default is 9.

        The mtime argument is an optional numeric timestamp to be written
        to the last modification time field in the stream when compressing.
        If omitted or None, the current time is used.

        """

        self.thread = thread
        self.read_blocks = None
        if mode and ('t' in mode or 'U' in mode):
            raise ValueError("Invalid mode: {!r}".format(mode))
        if mode and 'b' not in mode:
            mode += 'b'
        if fileobj is None:
            fileobj = self.myfileobj = builtins.open(filename, mode or 'rb', blocksize)
        if filename is None:
            filename = getattr(fileobj, 'name', '')
            if not isinstance(filename, (str, bytes)):
                filename = ''
        if mode is None:
            mode = getattr(fileobj, 'mode', 'rb')

        if mode.startswith('r'):
            self.mode = READ
            if not self.thread:
                self.thread = os.cpu_count() // 2 # cores number
            self.raw = _MulitGzipReader(fileobj, thread=self.thread, max_block_size=blocksize)
            self._buffer = io.BufferedReader(self.raw, blocksize)
            self.name = filename
            self.index = []

        elif mode.startswith(('w', 'a', 'x')):
            self.mode = WRITE
            if not self.thread:
                # thread is None or 0, use all available CPUs
                self.thread = os.cpu_count()
            self._init_write(filename)
            self.compress = zlib.compressobj(compresslevel,
                                             zlib.DEFLATED,
                                             -zlib.MAX_WBITS,
                                             zlib.DEF_MEM_LEVEL,
                                             0)
            self._write_mtime = mtime
            self.compresslevel = compresslevel
            self.blocksize = blocksize # use 20M blocksize as default
            self.pool = Pool(self.thread)
            self.pool_result = []
            self.small_buf = io.BytesIO()
        else:
            raise ValueError("Invalid mode: {!r}".format(mode))

        self.fileobj = fileobj

    def __repr__(self):
        s = repr(self.fileobj)
        return '<pgzip ' + s[1:-1] + ' ' + hex(id(self)) + '>'

    def _write_gzip_header(self):
        ## ignored to write original header
        pass

    def _compress_func(self, data, pdata=None):
        """
            Compress data with zlib deflate algorithm.
            Input:
                data: btyes object of input data
                pdata: exists small buffer data
            Return:
                tuple of (Buffered compressed data,
                          Major compressed data,
                          Rest data after flush buffer,
                          CRC32,
                          Original size)
        """
        cpr = zlib.compressobj(self.compresslevel,
                               zlib.DEFLATED,
                               -zlib.MAX_WBITS,
                               9, # use memory level 9 > zlib.DEF_MEM_LEVEL (8) for better performance
                               0)
        if pdata:
            prefix_bytes = cpr.compress(pdata)
        body_bytes = cpr.compress(data)
        rest_bytes = cpr.flush()
        if pdata:
            crc = zlib.crc32(data, zlib.crc32(pdata))
            return (prefix_bytes, body_bytes, rest_bytes, crc, pdata.nbytes + data.nbytes)
        else:
            crc = zlib.crc32(data)
            return (b'', body_bytes, rest_bytes, crc, data.nbytes)

    def write(self, data):
        self._check_not_closed()
        if self.mode != WRITE:
            import errno
            raise OSError(errno.EBADF, "write() on read-only GzipFile object")

        if self.fileobj is None:
            raise ValueError("write() on closed GzipFile object")

        data = memoryview(data)
        length = data.nbytes

        if length == 0:
            return length
        elif length >= self.blocksize:
            if length < 2 * self.blocksize:
                # use sigle thread
                self._compress_block_async(data)
            else:
                for st in range(0, length, self.blocksize):
                    self._compress_block_async(data[st: st+self.blocksize])
                    self._flush_pool()
        elif length < self.blocksize:
            self.small_buf.write(data)
            if self.small_buf.tell() >= self.blocksize:
                self._compress_async(self.small_buf.getbuffer())
                self.small_buf = io.BytesIO()
        self._flush_pool()
        return length

    def _compress_async(self, data, pdata=None):
        return self.pool_result.append(self.pool.apply_async(self._compress_func, args=(data, pdata)))

    def _compress_block_async(self, data):
        if self.small_buf.tell() != 0:
            self._compress_async(data, self.small_buf.getbuffer())
            self.small_buf = io.BytesIO()
        else:
            self._compress_async(data)

    def _flush_pool(self, force=False):
        if len(self.pool_result) <= self.thread and not force:
            return 0
        length = 0
        if force:
            flushSize = len(self.pool_result)
        else:
            flushSize = len(self.pool_result) - self.thread
        for i in range(flushSize):
            cdata = self.pool_result.pop(0).get()
            length += self._write_member(cdata)
            # (bodyBytes, resBytes, crc, oriSize) = rlt.get()
            # compressRlt = rlt.get()
        return length

    def _write_member(self, cdata):
        """
            Write a compressed data as a complete gzip member
            Input:
                cdata:
                    compressed data, a tuple of compressed result returned by _compress_func()
            Return:
                size of member
        """
        size = self._write_member_header(len(cdata[0]) + len(cdata[1]) + len(cdata[2]), cdata[4])
        self.fileobj.write(cdata[0])                   # buffer data
        self.fileobj.write(cdata[1])                   # body data
        self.fileobj.write(cdata[2])                   # rest data
        write32u(self.fileobj, cdata[3])               # CRC32
        write32u(self.fileobj, cdata[4] & 0xffffffff)  # raw data size in 32bits
        return size

    def _write_member_header(self, compressed_size, raw_size):
        self.fileobj.write(b'\037\213')             # magic header, 2 bytes
        self.fileobj.write(b'\010')                 # compression method, 1 byte
        try:
            # RFC 1952 requires the FNAME field to be Latin-1. Do not
            # include filenames that cannot be represented that way.
            fname = os.path.basename(self.name)
            if not isinstance(fname, bytes):
                fname = fname.encode('latin-1')
            if fname.endswith(b'.gz'):
                fname = fname[:-3]
        except UnicodeEncodeError:
            fname = b''
        flags = FEXTRA
        if fname:
            flags |= FNAME
        self.fileobj.write(chr(flags).encode('latin-1'))  # flags, 1 byte
        mtime = self._write_mtime
        if mtime is None:
            mtime = time.time()
        write32u(self.fileobj, int(mtime))          # modified time, 4 bytes
        self.fileobj.write(b'\002')                 # fixed flag (maximum compression), 1 byte
        self.fileobj.write(b'\377')                 # OS (unknown), 1 byte

        # write extra flag for indexing
        # XLEN, 8 bytes
        self.fileobj.write(b'\x08\x00')             # extra flag len, 2 bytes
        # EXTRA FLAG FORMAT:
        # +---+---+---+---+---+---+---+---+
        # |SI1|SI2|  LEN  |  MEMBER SIZE  |
        # +---+---+---+---+---+---+---+---+
        # SI1, SI2:      Subfield ID, 'IG' (Indexed Gzip file)
        # LEN:           Length of subfield body, always 4 (bytes)
        # MEMBER SIZE:   The size of current member
        self.fileobj.write(SID)                   # subfield ID (IG), 2 bytes
        # LEN: 4 bytes
        self.fileobj.write(b'\x04\x00')             # subfield len (4), 2 bytes
        # compressed data size: 16 + 4 + len(fname) + 1 + data + 8
        #                       header + member size + filename with zero end + data block + CRC32 and ISIZE
        member_size = 20 + len(fname) + 1 + compressed_size + 8
        if not fname:
            member_size -= 1
        self.fileobj.write(struct.pack("<I", member_size)) # member size, 4 bytes
        if fname:
            self.fileobj.write(fname + b'\000')
        return member_size

    def get_index(self):
        """
            Index Format:
                0: Start offset
                1: Block size
                2: Raw size
                3: Comment (If exists)
        """
        if self.mode != READ:
            raise OSError("READ mode is required for get_index.")
        self.index = []
        raw_pos = self.myfileobj.tell()
        self.myfileobj.seek(0)
        while True:
            commentByte = b""
            self.myfileobj.seek(3, 1)
            fByte = self.myfileobj.read(1)
            if not fByte:
                break
            flag, = struct.unpack("<B", fByte)
            self.myfileobj.seek(8, 1)
            extra_flag = self.myfileobj.read(8)
            if not extra_flag:
                break
            sid, _, msize = struct.unpack("<2sHI", extra_flag)
            if sid != SID:
                raise OSError("Invaild Indexed GZIP format")
            if flag & FNAME:
                while True:
                    s = self.myfileobj.read(1)
                    if not s or s==b'\000':
                        break
            if flag & FCOMMENT:
                while True:
                    s = self.myfileobj.read(1)
                    if not s or s==b'\000':
                        break
                    commentByte += s
            if not self.index:
                self.index.append([0, msize, 0, commentByte.decode()])
            else:
                self.index.append([self.index[-1][0] + self.index[-1][1], msize, 0, commentByte.decode()])
            self.myfileobj.seek(self.index[-1][0] + self.index[-1][1] - 4)
            isize, = struct.unpack("<I", self.myfileobj.read(4))
            self.index[-1][2] = isize
        self.myfileobj.seek(raw_pos)
        return self.index

    def show_index(self):
        if not self.index:
            self.get_index()
        block_id = 0
        print("#ID\tStart\tBlockSize\tRawSize\tComment")
        for e in self.index:
            print(block_id, *e, sep="\t")
            block_id += 1

    def build_index(self, idx_file=None):
        if not idx_file:
            idx_file = self.name + ".idx"
        if not self.index:
            self.get_index()
        block_id = 0
        with builtins.open(idx_file, 'w') as fh:
            print("#ID\tStart\tBlockSize\tRawSize\tComment", file=fh)
            for e in self.index:
                if not e[2]:
                    continue
                print(block_id, *e, sep="\t", file=fh)
                block_id += 1
        return self.index

    def load_index(self, idx_file):
        self.index = []
        with builtins.open(idx_file, 'r') as fh:
            for line in fh:
                info = line.split()
                if not info or info[0].startswith('#'):
                    continue
                self.index.append([int(info[1]), int(info[2]), int(info[3]), info[4]])
        return self.index

    def set_read_blocks(self, block_ids):
        self.raw.set_block_iter([self.index[x][0] for x in block_ids])

    def set_read_blocks_by_name(self, block_names):
        """
            If file use comment to record the name of blocks,
            set read blocks to given list of block name.

            * The order of reading will follow the block
              order in compressed file instead of input block_names
        """
        block_name_set = set(block_names)
        self.raw.set_block_iter([x[0] for x in self.index if x[3] in block_name_set])

    def clear_read_blocks(self):
        self.raw.clear_block_iter()

    def close(self):
        fileobj = self.fileobj
        if fileobj is None:
            return
        try:
            if self.mode == WRITE:
                if self.small_buf.tell() != 0:
                    self._compress_async(self.small_buf.getbuffer())
                    self.small_buf = io.BytesIO()
                self._flush_pool(force=True)
            elif self.mode == READ:
                self._buffer.close()
        finally:
            self.fileobj = None
            myfileobj = self.myfileobj
            if myfileobj:
                self.myfileobj = None
                myfileobj.close()

            if self.mode == WRITE:
                self.pool.close()
                self.pool.join()
            elif self.mode == READ:
                self.raw.close()

    def flush(self):
        self._check_not_closed()
        if self.mode == WRITE:
            self._flush_pool(force=True)
            self.fileobj.flush()

class _MulitGzipReader(_GzipReader):
    def __init__(self, fp, thread=4, max_block_size=5*10**8):
        super().__init__(fp)

        self.memberidx = [] # list of tuple (memberSize, rawTxtSize)
        self._is_IG_member = False
        self._header_size = 0
        self.max_block_size = max_block_size
        self.thread = thread
        self._read_pool = []
        self._pool = Pool(self.thread)
        self._block_buff = b""
        self._block_buff_pos = 0
        self._block_buff_size = 0
        self._is_eof = False
        self._raw_fp = fp
        self.block_start_iter = None

    def _decompress_func(self, data, rcrc, rsize):
        """
            Decompress data and return exact bytes of plain text
            Input:
                data: compressed data
                rcrc: raw crc32
                rsize: raw data size
            Return:
                body_bytes: bytes object of decompressed data
                rsize: raw data size
                crc: crc32 calculated by decompressed data
                rcrc: raw crc32 in compressed file
        """
        dpr = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        ## FIXME: case when raw data size > 4 GB, rsize is just the mod of 4G
        ## not a good idea to read all of them in memory
        body_bytes = dpr.decompress(data, rsize)
        crc = zlib.crc32(body_bytes)
        if dpr.unconsumed_tail != b"":
            body_bytes += dpr.unconsumed_tail
            crc = zlib.crc32(dpr.unconsumed_tail, crc)
        return (body_bytes, rsize, crc, rcrc)

    def _decompress_async(self, data, rcrc, rsize):
        self._read_pool.append(self._pool.apply_async(self._decompress_func, args=(data, rcrc, rsize)))

    def _read_gzip_header(self):
        magic = self._fp.read(2)
        if magic == b'':
            return False

        if magic != b'\037\213':
            raise OSError('Not a gzipped file (%r)' % magic)

        (method, flag,
         self._last_mtime) = struct.unpack("<BBIxx", self._read_exact(8))
        if method != 8:
            raise OSError('Unknown compression method')

        if flag & FEXTRA:
            # Read & discard the extra field, if present
            extra_len, sid = struct.unpack("<H2s", self._read_exact(4))
            if sid == SID:
                _, msize = struct.unpack("<HI" ,self._read_exact(extra_len - 2))
                self.memberidx.append(msize)
                self._is_IG_member = True
                # print("block", len(self.memberidx), msize, rsize)
                self._header_size = 20 # fixed header + FEXTRA
            else:
                self._is_IG_member = False

        if flag & FNAME:
            # Read and discard a null-terminated string containing the filename
            while True:
                s = self._fp.read(1)
                self._header_size += 1
                if not s or s==b'\000':
                    break
        if flag & FCOMMENT:
            # Read and discard a null-terminated string containing a comment
            while True:
                s = self._fp.read(1)
                self._header_size += 1
                if not s or s==b'\000':
                    break
        if flag & FHCRC:
            self._read_exact(2)     # Read & discard the 16-bit header CRC
            self._header_size += 2
        return True

    def read(self, size=-1):
        if size < 0:
            return self.readall()
        # size=0 is special because decompress(max_length=0) is not supported
        if not size:
            return b""

        # For certain input data, a single
        # call to decompress() may not return
        # any data. In this case, retry until we get some data or reach EOF.
        while True:
            if self.block_start_iter and self.thread:
                try:
                    self._fp.seek(next(self.block_start_iter))
                except Exception:
                    self.clear_block_iter()
                    self._fp.seek(0, 2)
                    continue
            if self._decompressor.eof:
                # Ending case: we've come to the end of a member in the file,
                # so finish up this member, and read a new gzip header.
                # Check the CRC and file size, and set the flag so we read
                # a new member
                self._read_eof()
                self._new_member = True
                self._decompressor = self._decomp_factory(
                    **self._decomp_args)

            if self._new_member and self.thread:
                # If the _new_member flag is set, we have to
                # jump to the next member, if there is one.
                self._init_read()
                if not self._read_gzip_header():
                    self._size = self._pos
                    self._is_eof = True
                else:
                    self._new_member = False

                    if self._is_IG_member:
                        # 8 bytes for crc32 and isize
                        cpr_size = self.memberidx[-1] - self._header_size - 8
                        self._decompress_async(self._fp.read(cpr_size),
                                               *self._read_eof_crc())
                        self.thread -= 1
                        self._new_member = True
                        continue

            if self._block_buff_pos + size <= self._block_buff_size:
                st_pos = self._block_buff_pos
                self._block_buff_pos += size
                if self._block_buff_pos >= self._block_buff_size:
                    self._block_buff_pos = self._block_buff_size
                return self._block_buff[st_pos:self._block_buff_pos]
            elif self._read_pool:
                block_read_rlt = self._read_pool.pop(0).get()
                self.thread += 1
                # check decompressed data size
                if len(block_read_rlt[0]) != block_read_rlt[1]:
                    raise OSError("Incorrect length of data produced")
                # check raw crc32 == decompressed crc32
                if block_read_rlt[2] != block_read_rlt[3]:
                    raise OSError("CRC check failed {:s} != {:s}".format(
                        block_read_rlt[3], block_read_rlt[2]
                    ))
                self._block_buff = self._block_buff[self._block_buff_pos:] + block_read_rlt[0]
                self._block_buff_size = len(self._block_buff)
                self._block_buff_pos = min(size, self._block_buff_size)
                return self._block_buff[:size] # FIXME: fix issue when size > len(self._block_buff)
            elif self._block_buff_pos != self._block_buff_size:
                # still something in self._block_buff
                st_pos = self._block_buff_pos
                self._block_buff_pos = self._block_buff_size
                return self._block_buff[st_pos:]
            elif self._is_eof:
                return b""

            # Read a chunk of data from the file
            buf = self._fp.read(io.DEFAULT_BUFFER_SIZE)

            uncompress = self._decompressor.decompress(buf, size)
            if self._decompressor.unconsumed_tail != b"":
                self._fp.prepend(self._decompressor.unconsumed_tail)
            elif self._decompressor.unused_data != b"":
                # Prepend the already read bytes to the fileobj so they can
                # be seen by _read_eof() and _read_gzip_header()
                self._fp.prepend(self._decompressor.unused_data)

            if uncompress != b"":
                break
            if buf == b"":
                raise EOFError("Compressed file ended before the "
                               "end-of-stream marker was reached")

        self._add_read_data( uncompress )
        self._pos += len(uncompress)
        return uncompress

    def _read_eof_crc(self):
        """
            Get crc32 and isize without checking
        """
        crc32, isize = struct.unpack("<II", self._read_exact(8))

        # Gzip files can be padded with zeroes and still have archives.
        # Consume all zero bytes and set the file position to the first
        # non-zero byte. See http://www.gzip.org/#faq8
        c = b"\x00"
        while c == b"\x00":
            c = self._fp.read(1)
        if c:
            self._fp.prepend(c)
        return (crc32, isize)

    def set_block_iter(self, block_start_list):
        self.block_start_iter = iter(block_start_list)

    def clear_block_iter(self):
        self.block_start_iter = None
