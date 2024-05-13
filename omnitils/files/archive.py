"""
* Utils: Compressing and Decompressing Archives
"""
# Standard Library
import bz2
from contextlib import suppress
import gzip
import gc
import lzma
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from threading import Lock
from typing import Optional, Callable
import zipfile

# Third Party Imports
from loguru import logger
from tqdm import tqdm
import py7zr
from py7zr import SevenZipFile, FILTER_LZMA, FILTER_X86

# Local Imports
from omnitils.enums import StrConstant
from omnitils.strings import str_to_bool_safe

# Locking mechanism
ARCHIVE_LOCK = Lock()

"""
* Enums
"""


class ArchType(StrConstant):
    """Recognized archive extension types."""
    Zip = '.zip'
    GZip = '.gz'
    XZip = '.xz'
    BZip2 = '.bz2'
    SevenZip = '.7z'
    TarGZip = '.tar.gz'
    TarXZip = '.tar.xz'
    TarBZip2 = '.tar.bz2'
    TarSevenZip = '.tar.xz'


class WordSize(StrConstant):
    """Word Size for 7z compression."""
    WS16 = "16"
    WS24 = "24"
    WS32 = "32"
    WS48 = "48"
    WS64 = "64"
    WS96 = "96"
    WS128 = "128"


class DictionarySize(StrConstant):
    """Dictionary Size for 7z compression."""
    DS32 = "32"
    DS48 = "48"
    DS64 = "64"
    DS96 = "96"
    DS128 = "128"
    DS192 = "192"
    DS256 = "256"
    DS384 = "384"
    DS512 = "512"
    DS768 = "768"
    DS1024 = "1024"
    DS1536 = "1536"


"""
* Compression Utils
"""


def compress_7z_py(
    path_in: Path,
    path_out: Optional[Path] = None,
    filters: Optional[list[dict[str, int]]] = None
) -> Optional[Path]:
    """Compress a target file to a target 7z archive using the py7zr module.

    Args:
        path_in: File to compress.
        path_out: Path to the archive to be saved. Use 'compressed' subdirectory if not provided.
        filters: Filters used when initializing the SevenZipFile object, uses LZMA+BCJ by default.

    Returns:
        Path to the resulting 7z archive if successful, otherwise None.
    """
    lzma_bcj = filters or [{'id': FILTER_X86}, {'id': FILTER_LZMA}]
    with SevenZipFile(path_out, 'w', filters=lzma_bcj) as z:
        z.write(path_in)
    return path_out


def compress_7z_7zip(
    path_in: Path,
    path_out: Optional[Path] = None,
    compress_level: int = 9,
    word_size: WordSize = WordSize.WS16,
    dict_size: DictionarySize = DictionarySize.DS1536,

) -> Optional[Path]:
    """Compress a target file to a target 7z archive using the 7-Zip CLI.

    Notes:
        Compressing using the 7-Zip CLI is relevantly faster than compressing with the py7zr
            package, but required 7-Zip be installed on the host system.

    Args:
        path_in: File to compress.
        path_out: Path to the archive to be saved. Use 'compressed' subdirectory if not provided.
        compress_level: Compression level to use (1 to 9), default is 9.
        word_size: Word size value to use for the compression, default is 16.
        dict_size: Dictionary size value to use for the compression, default is 1536.

    Returns:
        Path to the resulting 7z archive if successful, otherwise None.
    """
    null_device = open(os.devnull, 'w')
    subprocess.run([
        "7z", "a", "-t7z", "-m0=LZMA",
        f"-mx={compress_level}",
        f"-md={dict_size}M",
        f"-mfb={word_size}",
        str(path_out),
        str(path_in)
    ], stdout=null_device, stderr=null_device)
    return path_out


def compress_7z(
    path_in: Path,
    path_out: Optional[Path] = None,
    use_7zip: bool = False,
    compress_level: int = 9,
    word_size: WordSize = WordSize.WS16,
    dict_size: DictionarySize = DictionarySize.DS1536,
) -> Optional[Path]:
    """Compress a target file and save it as a 7z archive to the output directory.

    Args:
        path_in: File to compress.
        path_out: Path to the archive to be saved. Use 'compressed' subdirectory if not provided.
        use_7zip: Whether to use the 7zip CLI to perform the compression, defaults to False. Can also be flagged
            using the USE_7ZIP environment variable (string bool).
        compress_level: Compression level to use (1 to 9). Only used with 7-Zip CLI, default is 9.
        word_size: Word size value to use for the compression. Only used with 7-Zip CLI, default is 16.
        dict_size: Dictionary size value to use for the compression. Only used with 7-Zip CLI, default is 1536.

    Returns:
        Path to the resulting 7z archive if successful, otherwise None.
    """
    # Define the output file path
    path_out = path_out or Path(path_in.parent, '.compressed', path_in.name)
    path_out = path_out.with_suffix('.7z')

    # Compress the file
    with suppress(Exception):

        # Compress with 7-Zip
        if use_7zip or str_to_bool_safe(os.environ.get('USE_7ZIP', '0')):
            return compress_7z_7zip(
                path_in=path_in,
                path_out=path_out,
                compress_level=compress_level,
                word_size=word_size,
                dict_size=dict_size)

        # Compress with py7zr
        return compress_7z_py(
            path_in=path_in,
            path_out=path_out)

    # Error occurred, None returned
    return logger.exception(f'Unable to compress file: {path_in.name}')


def compress_7z_all(
    path_in: Path,
    path_out: Path = None,
    word_size: WordSize = WordSize.WS16,
    dict_size: DictionarySize = DictionarySize.DS1536
) -> None:
    """Compress every file inside `path_in` directory as 7z archives, then output
    those archives in the `path_out`.

    Args:
        path_in: Directory containing files to compress.
        path_out: Directory to place the archives. Use a subdirectory 'compressed' if not provided.
        word_size: Word size value to use for the compression.
        dict_size: Dictionary size value to use for the compression.
    """
    # Use "compressed" subdirectory if not provided, ensure output directory exists
    path_out = path_out or Path(path_in, '.compressed')
    path_out.mkdir(mode=777, parents=True, exist_ok=True)

    # Get a list of all .psd files in the directory
    files = [
        Path(path_in, n) for n in os.listdir(path_in)
        if Path(path_in, n).is_file()]

    # Compress each file
    with tqdm(total=len(files), desc="Compressing files", unit="file") as pbar:
        for f in files:
            p = (path_out / f.name).with_suffix('.7z')
            pbar.set_description(f.name)
            compress_7z(
                path_in=f,
                path_out=p,
                word_size=word_size,
                dict_size=dict_size)
            pbar.update()


"""
* Decompression Utils
"""


def unpack_zip(path: Path) -> None:
    """Unpack target 'zip' archive.

    Args:
        path: Path to the archive.

    Raises:
        FileNotFoundError: If archive couldn't be located.
    """
    if not path.is_file():
        raise FileNotFoundError(f'Archive not found: {str(path)}')
    with zipfile.ZipFile(path) as z:
        z.extractall(path=path.parent)


def unpack_gz(path: Path) -> None:
    """Unpack target 'gz' archive.

    Args:
        path: Path to the archive.

    Raises:
        FileNotFoundError: If archive couldn't be located.
    """
    if not path.is_file():
        raise FileNotFoundError(f'Archive not found: {str(path)}')
    output = path.parent / path.name[:-3]
    with gzip.open(path) as z:
        with open(output, 'wb') as f:
            shutil.copyfileobj(z, f)


def unpack_xz(path: Path) -> None:
    """Unpack target 'xz' archive.

    Args:
        path: Path to the archive.

    Raises:
        FileNotFoundError: If archive couldn't be located.
    """
    if not path.is_file():
        raise FileNotFoundError(f'Archive not found: {str(path)}')
    output = path.parent / path.name[:-3]
    with lzma.open(path) as z:
        with open(output, 'wb') as f:
            shutil.copyfileobj(z, f)


def unpack_bz2(path: Path) -> None:
    """Unpack target 'bz2' archive.

    Args:
        path: Path to the archive.

    Raises:
        FileNotFoundError: If archive couldn't be located.
    """
    if not path.is_file():
        raise FileNotFoundError(f'Archive not found: {str(path)}')
    output = path.parent / path.name[:-3]
    with bz2.open(path) as z:
        with open(output, 'wb') as f:
            shutil.copyfileobj(z, f)


def unpack_7z(path: Path) -> None:
    """Unpack target '7z' archive.

    Args:
        path: Path to the archive.

    Raises:
        FileNotFoundError: If archive couldn't be located.
    """
    if not path.is_file():
        raise FileNotFoundError(f'Archive not found: {str(path)}')
    with py7zr.SevenZipFile(path, 'r') as z:
        z.extractall(path=path.parent)


def unpack_tar(path: Path, mode: str = 'gz'):
    """Unpack target 'tar' archive of a given type.

    Args:
        path: Path to the archive.
        mode: Mode to use when unpacking, i.e. type of archive it is (gz, xz, etc). Defaults to `gz`.

    Raises:
        FileNotFoundError: If archive couldn't be located.
    """
    if not path.is_file():
        raise FileNotFoundError(f'Archive not found: {str(path)}')
    with tarfile.open(path, f'r:{mode}') as z:
        z.extractall(path=path.parent)


def unpack_tar_gz(path: Path) -> None:
    """Shorthand function for `unpack_tar` targeting a `tar.gz` archive."""
    unpack_tar(path, mode='gz')


def unpack_tar_xz(path: Path) -> None:
    """Shorthand function for `unpack_tar` targeting a `tar.xz` archive."""
    unpack_tar(path, mode='xz')


def unpack_tar_bz2(path: Path) -> None:
    """Shorthand function for `unpack_tar` targeting a `tar.bz2` archive."""
    unpack_tar(path, mode='bz2')


def unpack_archive(path: Path, remove: bool = True, thread_lock: Optional[Lock] = None) -> None:
    """Unpack an archive using the correct methodology based on its extension.

    Args:
        path: Path to the archive.
        remove: Whether to remove the archive after unpacking.
        thread_lock: Optional Lock object used to prevent concurrent unpacking, will use
            default Lock object if not provided.

    Raises:
        FileNotFoundError: If archive couldn't be located.
    """
    action_map: dict[str, Callable] = {
        ArchType.Zip: unpack_zip,
        ArchType.GZip: unpack_gz,
        ArchType.XZip: unpack_xz,
        ArchType.TarGZip: unpack_tar_gz,
        ArchType.TarXZip: unpack_tar_xz,
        ArchType.SevenZip: unpack_7z,
        ArchType.TarSevenZip: unpack_7z
    }
    if path.suffix not in action_map:
        return
    action = action_map[path.suffix]
    if thread_lock is None:
        thread_lock = ARCHIVE_LOCK
    with thread_lock:
        _ = action(path)
    if remove:
        os.remove(path)
    gc.collect()
