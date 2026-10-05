#!/usr/bin/env python3
"""
Download a small slice of one KITTI raw drive: the calibration files for its
date plus a handful of frames from the sensors you need.

Instead of downloading the whole ~0.4-1 GB drive zip, this uses HTTP range
requests to read the zip's table of contents remotely and fetch only the
selected files. Ten frames of camera 2 + LiDAR is roughly 25-30 MB.

The result matches the layout pykitti.raw expects:

    <out>/2011_09_26/calib_cam_to_cam.txt
    <out>/2011_09_26/calib_velo_to_cam.txt
    <out>/2011_09_26/calib_imu_to_velo.txt
    <out>/2011_09_26/2011_09_26_drive_0001_sync/image_02/...
    <out>/2011_09_26/2011_09_26_drive_0001_sync/velodyne_points/...
    <out>/2011_09_26/2011_09_26_drive_0001_sync/oxts/...

Usage:
    python download_kitti_sample.py --out data/kitti
    python download_kitti_sample.py --out data/kitti --drive 0005 --start 20 --num-frames 5
    python download_kitti_sample.py --out data/kitti --full   # fallback: whole zip

Only the Python standard library is required.
"""
import argparse
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

BASE_URL = "https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data"

# image_02 = left colour camera, velodyne_points = LiDAR.
# oxts (GPS/IMU) is tiny, and pykitti reads its timestamps when it initialises.
DEFAULT_SENSORS = ["image_02", "velodyne_points", "oxts"]


class HttpRangeFile(io.RawIOBase):
    """A read-only, seekable file object backed by HTTP range requests."""

    def __init__(self, url):
        self.url = url
        self.pos = 0
        self.bytes_fetched = 0
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req) as r:
            self.size = int(r.headers["Content-Length"])

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            self.pos = offset
        elif whence == io.SEEK_CUR:
            self.pos += offset
        elif whence == io.SEEK_END:
            self.pos = self.size + offset
        return self.pos

    def readinto(self, buf):
        if self.pos >= self.size or len(buf) == 0:
            return 0
        end = min(self.pos + len(buf), self.size) - 1
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end}"})
        with urllib.request.urlopen(req) as r:
            if r.status != 206:
                raise RuntimeError("Server ignored the Range header; rerun with --full")
            data = r.read()
        n = len(data)
        buf[:n] = data
        self.pos += n
        self.bytes_fetched += n
        return n


def open_remote_zip(url):
    raw = HttpRangeFile(url)
    # Small buffer: zipfile does many tiny header reads, and big member reads
    # bypass the buffer anyway, so 64 KiB keeps wasted bytes low.
    return zipfile.ZipFile(io.BufferedReader(raw, buffer_size=64 * 1024)), raw


def download_full(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"  already downloaded: {dest}")
        return dest

    def hook(blocks, block_size, total):
        done = blocks * block_size
        if total > 0:
            pct = min(100, done * 100 / total)
            print(f"\r  {done / 1e6:7.1f} / {total / 1e6:.1f} MB ({pct:5.1f}%)", end="", flush=True)

    tmp = dest.with_suffix(".part")
    urllib.request.urlretrieve(url, tmp, reporthook=hook)
    tmp.rename(dest)
    print()
    return dest


def is_wanted(name, sensors, frames):
    """Decide whether a member of the drive zip should be extracted."""
    if name.endswith("/"):
        return False
    parts = name.split("/")
    if "data" in parts:
        # .../<sensor>/data/0000000042.png
        i = parts.index("data")
        sensor = parts[i - 1]
        stem = Path(parts[-1]).stem
        return sensor in sensors and stem.isdigit() and int(stem) in frames
    # Small metadata files: <sensor>/timestamps.txt, oxts/dataformat.txt, ...
    return len(parts) >= 2 and parts[-2] in sensors and name.endswith(".txt")


def extract(zf, names, out_dir):
    count = 0
    for name in names:
        target = out_dir / name
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(name) as src, open(target, "wb") as dst:
            dst.write(src.read())
        count += 1
        print(f"  {name}")
    return count


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path, default=Path("data/kitti"), help="base directory (pykitti basedir)")
    p.add_argument("--date", default="2011_09_26")
    p.add_argument("--drive", default="0001", help="zero-padded drive number, e.g. 0001")
    p.add_argument("--start", type=int, default=0, help="first frame index")
    p.add_argument("--num-frames", type=int, default=10)
    p.add_argument("--sensors", nargs="+", default=DEFAULT_SENSORS)
    p.add_argument("--full", action="store_true", help="download the whole drive zip instead of using range requests")
    p.add_argument("--base-url", default=BASE_URL, help="override the download host (if the public links move)")
    args = p.parse_args()

    drive_name = f"{args.date}_drive_{args.drive}"
    calib_url = f"{args.base_url}/{args.date}_calib.zip"
    drive_url = f"{args.base_url}/{drive_name}/{drive_name}_sync.zip"
    frames = set(range(args.start, args.start + args.num_frames))
    args.out.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Calibration: {calib_url}")
        zf, raw = open_remote_zip(calib_url)
        with zf:
            extract(zf, [n for n in zf.namelist() if n.endswith(".txt")], args.out)

        print(f"Drive: {drive_url}")
        if args.full:
            local = download_full(drive_url, args.out / "_zips" / f"{drive_name}_sync.zip")
            zf, raw = zipfile.ZipFile(local), None
        else:
            zf, raw = open_remote_zip(drive_url)
            print(f"  remote zip is {raw.size / 1e6:.0f} MB; fetching only the selected files")
        with zf:
            wanted = sorted(n for n in zf.namelist() if is_wanted(n, set(args.sensors), frames))
            if not any("/data/" in n for n in wanted):
                sys.exit("No matching frames found. Check --start/--num-frames against the drive length.")
            n = extract(zf, wanted, args.out)
        if raw is not None:
            print(f"  transferred {raw.bytes_fetched / 1e6:.1f} MB for {n} new files")
    except urllib.error.HTTPError as e:
        sys.exit(
            f"HTTP {e.code} for {e.url}\n"
            "If this is 403/404, the public links may have changed. Register at "
            "https://www.cvlibs.net/datasets/kitti/raw_data.php to get current download links, "
            "then pass the new location with --base-url."
        )

    print(f"\nDone. In Python:\n"
          f"  pykitti.raw('{args.out}', '{args.date}', '{args.drive}')")


if __name__ == "__main__":
    main()