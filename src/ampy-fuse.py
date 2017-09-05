import sys
import errno
import re

from ampy.pyboard import Pyboard, PyboardError

from fuse import FUSE, FuseOSError, Operations

class AmpyFuse(Operations):
    def __init__(self, device):
        self.board = Pyboard(device)
        self.board.enter_raw_repl()
        self.exec('import os')

    #
    # Ampy methods
    #

    def exec(self, command):
        self.board.exec(command)

    def eval(self, command):
        try:
            ret = self.board.eval(command).decode('utf-8')
        except PyboardError as e:
            pattern = re.compile(r'OSError: \[Errno (?P<error_number>\d+)\]',
                                 re.MULTILINE)
            error_message = e.args[2].decode('utf-8')
            match = pattern.search(error_message)
            if match:
                error_number = int(match.group('error_number'))
                raise FuseOSError(error_number)
            else:
                raise
        else:
            return ret

    #
    # Filesystem methods
    #

    def access(self, path, mode):
        pass

    def chmod(self, path, mode):
        raise FuseOSError(201)

    def chown(self, path, uid, gid):
        raise FuseOSError(202)

    def getattr(self, path, fh=None):
        pattern = r'\((?P<st_mode>\d+), ' \
                  r'(?P<st_ino>\d+), ' \
                  r'(?P<st_dev>\d+), ' \
                  r'(?P<st_nlink>\d+), ' \
                  r'(?P<st_uid>\d+), ' \
                  r'(?P<st_gid>\d+), ' \
                  r'(?P<st_size>\d+), ' \
                  r'(?P<st_atime>\d+), ' \
                  r'(?P<st_mtime>\d+), ' \
                  r'(?P<st_ctime>\d+)\)'
        ret = self.eval("os.stat('{}')".format(path))
        attrs = re.match(pattern, ret).groupdict()
        return {k: int(v) for k, v in attrs.items()}

    def readdir(self, path, fh):
        ret = self.eval("os.listdir('{}')".format(path))
        return re.findall(r"'\s*([^']*?)\s*'", ret)

    def readlink(self, path):
        raise FuseOSError(205)

    def mknod(self, path, mode, dev):
        raise FuseOSError(206)

    def rmdir(self, path):
        raise FuseOSError(207)

    def mkdir(self, path, mode):
        raise FuseOSError(208)

    def statfs(self, path):
        pattern = r'\((?P<f_bsize>\d+), ' \
                  r'(?P<f_frsize>\d+), ' \
                  r'(?P<f_blocks>\d+), ' \
                  r'(?P<f_bfree>\d+), ' \
                  r'(?P<f_bavail>\d+), ' \
                  r'(?P<f_files>\d+), ' \
                  r'(?P<f_ffree>\d+), ' \
                  r'(?P<f_avail>\d+), ' \
                  r'(?P<f_flag>\d+), ' \
                  r'(?P<f_namemax>\d+)\)'
        ret = self.eval("os.statvfs('{}')".format(path))
        stats = re.match(pattern, ret).groupdict()
        return {k: int(v) for k, v in stats.items()}

    def unlink(self, path):
        raise FuseOSError(200)

    def symlink(self, name, target):
        raise FuseOSError(210)

    def rename(self, old, new):
        raise FuseOSError(211)

    def link(self, target, name):
        raise FuseOSError(212)

    def utimens(self, path, times=None):
        raise FuseOSError(213)

    def destroy(self, path):
        self.board.exit_raw_repl()
        self.board.close()

    #
    # File methods
    #

    def open(self, path, flags):
        raise FuseOSError(errno.EPERM)

    def create(self, path, mode, fi=None):
        raise FuseOSError(errno.EPERM)

    def read(self, path, length, offset, fh):
        raise FuseOSError(errno.EPERM)

    def write(self, path, buf, offset, fh):
        raise FuseOSError(errno.EPERM)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(errno.EPERM)

    def flush(self, path, fh):
        raise FuseOSError(errno.EPERM)

    def release(self, path, fh):
        raise FuseOSError(errno.EPERM)

    def fsync(self, path, fdatasync, fh):
        raise FuseOSError(errno.EPERM)


def main(device, mntpoint):
    FUSE(AmpyFuse(device), mntpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])