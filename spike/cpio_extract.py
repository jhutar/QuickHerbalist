"""Extract a cpio newc archive — bootstrap for rpm2cpio output (no cpio bin)."""

import os
import stat
import sys


def main():
    """Read cpio archive from argv[1], extract to argv[2]."""
    data = open(sys.argv[1], "rb").read()
    dest = sys.argv[2]
    pos = 0
    while data[pos : pos + 6] != b"TRAILER!":
        assert data[pos : pos + 6] == b"070701", f"bad header at {pos}"
        fields = [int(data[pos + 6 + j * 8 : pos + 6 + (j + 1) * 8], 16) for j in range(13)]
        file_size, name_size = fields[6], fields[11]
        mode = fields[1]
        name = data[pos + 110 : pos + 110 + name_size - 1].decode()
        body = (pos + 110 + name_size + 3) & ~3
        data_pad = (file_size + 3) & ~3
        pos = body + data_pad
        if name == "TRAILER!!!":
            break
        payload = data[body : body + file_size]
        if mode & 0o170000 == 0o120000:
            payload = payload.rstrip(b"\x00")
        target = os.path.join(dest, name)
        st = stat.S_IFMT(mode)
        if st == stat.S_IFDIR:
            os.makedirs(target, exist_ok=True)
        elif st == stat.S_IFLNK:
            os.makedirs(os.path.dirname(target) or dest, exist_ok=True)
            if os.path.lexists(target):
                os.remove(target)
            os.symlink(payload.decode(), target)
        elif st == stat.S_IFREG:
            os.makedirs(os.path.dirname(target) or dest, exist_ok=True)
            with open(target, "wb") as f:
                f.write(payload)
            os.chmod(target, mode & 0o7777)
        # other entry types (fifo, device): skipped, not needed


if __name__ == "__main__":
    main()
