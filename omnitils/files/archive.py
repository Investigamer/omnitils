"""
* Utils: Compressing and Decompressing Archives
"""
import bz2
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

from loguru import logger
from tqdm import tqdm
import py7zr
from py7zr import SevenZipFile, FILTER_LZMA2

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
    Tar = ".tar"
    TarGZip = '.tar.gz'
    TarXZip = '.tar.xz'
    TarBZip2 = '.tar.bz2'
    TarSevenZip = '.tar.7z'


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
    DS16 = "16"
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
* Private Utils
"""


def _archive_type(path: Path) -> ArchType | None:
    name = path.name.lower()

    if name.endswith(".tar.gz"):
        return ArchType.TarGZip
    if name.endswith(".tar.xz"):
        return ArchType.TarXZip
    if name.endswith(".tar.bz2"):
        return ArchType.TarBZip2
    if name.endswith(".tar.7z"):
        return ArchType.TarSevenZip
    if name.endswith(".zip"):
        return ArchType.Zip
    if name.endswith(".gz"):
        return ArchType.GZip
    if name.endswith(".xz"):
        return ArchType.XZip
    if name.endswith(".bz2"):
        return ArchType.BZip2
    if name.endswith(".7z"):
        return ArchType.SevenZip
    if name.endswith(".tar"):
        return ArchType.Tar
    return None


def _get_default_archive_path(path_in: Path, path_out: Path | None) -> tuple[Path, Path]:
    """Find a sane default path for a compressed file. Returns as (path_in, path_out)."""
    if path_out is not None:
        _path = path_out.with_suffix(".7z")
        _path.parent.mkdir(parents=True, exist_ok=True)
        return path_in, _path

    _path = (path_in.parent / ".compressed" / path_in.name).with_suffix(".7z")
    _path.parent.mkdir(parents=True, exist_ok=True)
    return path_in, _path


def _choose_7z_dict_size(path_in: Path) -> DictionarySize:
    """Choose a sane LZMA dictionary size from the input file size."""
    size_mib = max(1, path_in.stat().st_size // (1024 * 1024))

    if size_mib <= 16:
        return DictionarySize.DS64
    if size_mib <= 128:
        return DictionarySize.DS128
    if size_mib <= 512:
        return DictionarySize.DS256
    if size_mib <= 2048:
        return DictionarySize.DS512
    return DictionarySize.DS1024


def _choose_7z_word_size(
    compress_level: int,
    dict_size: DictionarySize,
) -> WordSize:
    """Choose a sane LZMA fast-bytes value (word size). 7-Zip's 7z defaults use
        FastBytes 32 for normal compression levels and 64 for higher compression levels.
    """
    dict_mib = int(dict_size)

    # Lean toward 64+ for harder compression
    if compress_level >= 7:
        if dict_mib >= 512:
            return WordSize.WS96
        return WordSize.WS64

    # Lean toward 32 for simple compression
    if compress_level >= 5:
        if dict_mib >= 256:
            return WordSize.WS48
        return WordSize.WS32
    return WordSize.WS32


def _build_py7zr_filters(
    path: Path,
    compress_level: int = 7,
    word_size: WordSize | None = None,
    dict_size: DictionarySize | None = None
) -> list[dict[str, int]]:
    resolved_level = max(1, min(9, compress_level))
    resolved_dict_mib: DictionarySize = dict_size or _choose_7z_dict_size(path)
    resolved_word: WordSize = word_size or _choose_7z_word_size(resolved_level, resolved_dict_mib)
    return [
        {
            "id": FILTER_LZMA2,
            "preset": resolved_level,
            "dict_size": int(str(resolved_dict_mib)) * 1024 * 1024,
            "nice_len": int(str(resolved_word))
        }
    ]


"""
* Compression Utils
"""


def compress_7z_py(
    path_in: Path,
    path_out: Path | None = None,
    compress_level: int = 7,
    word_size: WordSize | None = None,
    dict_size: DictionarySize | None = None,
    filters: Optional[list[dict[str, int]]] = None
) -> Path | None:
    """Compress a target file to a target 7z archive using the py7zr module.

    Args:
        path_in: File to compress.
        path_out: Path to the archive to be saved. Use '.compressed' subdirectory if not provided.
        compress_level: Compression level to use (1 to 9), default is 7.
        word_size: Word size value to use for the compression. If None, chosen automatically.
        dict_size: Dictionary size value to use for the compression. If None, chosen automatically.
        filters: Filters used when initializing the SevenZipFile object, advanced use only.

    Returns:
        Path to the resulting 7z archive if successful, otherwise None.
    """
    # Ensure we have a valid input and output path
    if not path_in.is_file():
        return None
    _path_in, _path_out = _get_default_archive_path(path_in, path_out)

    # Create a py7zr filter using provided compression and word/dict sizes
    compress_level = max(1, min(9, compress_level))
    resolved_filters = filters or _build_py7zr_filters(
        path=_path_in,
        compress_level=compress_level,
        word_size=word_size,
        dict_size=dict_size
    )

    with SevenZipFile(_path_out, 'w', filters=resolved_filters) as z:
        z.write(_path_in)
    return _path_out


def compress_7z_7zip(
    path_in: Path,
    path_out: Path | None = None,
    compress_level: int = 7,
    word_size: WordSize | None = None,
    dict_size: DictionarySize | None = None,
    cmd: str = "7z"
) -> Path | None:
    """Compress a target file to a target 7z archive using the 7-Zip CLI.

    Notes:
        Compressing using the 7-Zip CLI is generally much faster than py7zr,
        but requires 7-Zip to be installed on the host system.

    Args:
        path_in: File to compress.
        path_out: Path to the archive to be saved. Use '.compressed' subdirectory if not provided.
        compress_level: Compression level to use (1 to 9), default is 7.
        word_size: Word size value to use for the compression. If None, chosen automatically.
        dict_size: Dictionary size value to use for the compression. If None, chosen automatically.
        cmd: String used to invoke 7-Zip CLI.

    Returns:
        Path to the resulting 7z archive if successful, otherwise None.
    """
    # Ensure we have a valid input and output path
    if not path_in.is_file():
        return None
    _path_in, _path_out = _get_default_archive_path(path_in, path_out)

    # Use provided compression and dict/word sizes, or choose sane defaults
    compress_level = max(1, min(9, compress_level))
    resolved_dict_size = dict_size or _choose_7z_dict_size(_path_in)
    resolved_word_size = word_size or _choose_7z_word_size(
        compress_level=compress_level,
        dict_size=resolved_dict_size,
    )

    cmd_args = [
        cmd,
        "a",
        "-t7z",
        "-m0=LZMA2",
        f"-mx={compress_level}",
        f"-md={resolved_dict_size}M",
        f"-mfb={resolved_word_size}",
        str(_path_out),
        str(_path_in)
    ]

    try:
        with open(os.devnull, "w") as null_device:
            result = subprocess.run(
                cmd_args,
                stdout=null_device,
                stderr=null_device,
                check=False,
            )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return _path_out


# noinspection PyDeprecation
def compress_7z(
    path_in: Path,
    path_out: Path | None = None,
    use_7zip: bool | None = None,
    compress_level: int = 7,
    word_size: WordSize | None = None,
    dict_size: DictionarySize | None = None
) -> Path | None:
    """Compress a target file and save it as a 7z archive to the output directory. Will use 7-Zip if installed,
        otherwise falls back to py7zr.

    Args:
        path_in: File to compress.
        path_out: Path to the archive to be saved. Use '.compressed' subdirectory if not provided.
        use_7zip: Whether to try to use 7-Zip CLI to perform the compression. Can also be flagged
            using the USE_7ZIP environment variable (string bool). Defaults to True.
        compress_level: Compression level to use (1 to 9), default is 7.
        word_size: Word size value to use for the compression. If None, chosen automatically.
        dict_size: Dictionary size value to use for the compression. If None, chosen automatically.

    Returns:
        Path to the resulting 7z archive if successful, otherwise None.
    """
    # Ensure we have a valid input and output path
    if not path_in.is_file():
        return None
    _path_in, _path_out = _get_default_archive_path(path_in, path_out)

    try:
        if use_7zip is None:
            use_7zip = str_to_bool_safe(os.environ.get("USE_7ZIP", "1"))
        if use_7zip:
            exe = shutil.which("7z") or shutil.which("7za")
            if exe:
                result = compress_7z_7zip(
                    path_in=_path_in,
                    path_out=_path_out,
                    compress_level=compress_level,
                    word_size=word_size,
                    dict_size=dict_size,
                    cmd=exe
                )
                if result is not None:
                    return result

        return compress_7z_py(
            path_in=_path_in,
            path_out=_path_out,
            compress_level=compress_level,
            word_size=word_size,
            dict_size=dict_size)

    except OSError:
        logger.exception(f"Unable to compress file: {path_in.name}")
        return None


def compress_7z_all(
    path_in: Path,
    path_out: Path | None = None,
    use_7zip: bool | None = None,
    compress_level: int = 7,
    word_size: WordSize | None = None,
    dict_size: DictionarySize | None = None
) -> Path | None:
    """Compress every file inside `path_in` directory as 7z archives, then output
    those archives in the `path_out`.

    Args:
        path_in: Directory containing files to compress.
        path_out: Directory to place the archives. Use a subdirectory 'compressed' if not provided.
        use_7zip: Whether to try to use 7-Zip CLI to perform the compression, defaults to True. Can
            also be flagged using the USE_7ZIP environment variable (string bool).
        compress_level: Compression level to use (1 to 9), default is 7.
        word_size: Word size value to use for the compression. If None, chosen automatically.
        dict_size: Dictionary size value to use for the compression. If None, chosen automatically.

    Returns:
        Path to the directory each 7z archive is saved.
    """
    # Ensure we have a valid input and output path
    if not path_in.is_dir():
        return None
    if path_out is None:
        # Use ".compressed" subdirectory if not provided
        path_out: Path = path_in.parent / ".compressed" / path_in.name
    path_out.mkdir(parents=True, exist_ok=True)

    # Get a list of all files in the directory
    files = [
        Path(path_in, n) for n in os.listdir(path_in)
        if Path(path_in, n).is_file()
    ]

    # Compress each file
    with tqdm(total=len(files), desc="Compressing files", unit="file") as pbar:
        for f in files:
            p = (path_out / f.name).with_suffix('.7z')
            pbar.set_description(f.name)
            compress_7z(
                path_in=f,
                path_out=p,
                use_7zip=use_7zip,
                compress_level=compress_level,
                word_size=word_size,
                dict_size=dict_size)
            pbar.update()
    return path_out


"""
* Decompression Utils
"""


def unpack_zip(path: Path) -> Path:
    """Unpack a zip archive safely into its parent directory.

    Blocks absolute paths and path traversal outside the extraction root.

    Args:
        path: Path to the archive.

    Returns:
        Path to the directory containing extracted contents.

    Raises:
        FileNotFoundError: If archive couldn't be located.
        RuntimeError: If the archive contains an unsafe member path.
        zipfile.BadZipFile: If the archive is invalid.
    """
    output = path.parent.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Archive not found: {path}")

    with zipfile.ZipFile(path, "r") as zf:
        members = zf.infolist()

        for member in members:
            name = member.filename
            if "\x00" in name:
                raise RuntimeError(f"Unsafe null byte in zip archive member: {name}")

            member_path = Path(name)
            if member_path.is_absolute():
                raise RuntimeError(f"Unsafe absolute path in zip archive: {name}")

            # Extra guard for Windows-style drive-prefixed names
            if member_path.drive:
                raise RuntimeError(f"Unsafe drive path in zip archive: {name}")

            dest = (output / member_path).resolve()
            if output not in dest.parents and dest != output:
                raise RuntimeError(f"Path traversal detected in zip archive: {name}")
        zf.extractall(path=output)
    return output


def unpack_gz(path: Path) -> Path:
    """Unpack target 'gz' compressed file.

    Args:
        path: Path to the compressed file.

    Returns:
        Path to the decompressed file.

    Raises:
        FileNotFoundError: If file couldn't be located.
    """
    if not path.is_file():
        raise FileNotFoundError(f'Archive not found: {str(path)}')
    output = path.with_suffix("")
    with gzip.open(path) as fr, open(output, 'wb') as fw:
        shutil.copyfileobj(fr, fw)  # noqa
    return output


def unpack_xz(path: Path) -> Path:
    """Unpack target 'xz' archive.

    Args:
        path: Path to the compressed file.

    Returns:
        Path to the decompressed file.

    Raises:
        FileNotFoundError: If file couldn't be located.
    """
    if not path.is_file():
        raise FileNotFoundError(f'Archive not found: {str(path)}')
    output = path.with_suffix("")
    with lzma.open(path) as fr, open(output, 'wb') as fw:
        shutil.copyfileobj(fr, fw)  # noqa
    return output


def unpack_bz2(path: Path) -> Path:
    """Unpack target 'bz2' archive.

    Args:
        path: Path to the compressed file.

    Returns:
        Path to the decompressed file.

    Raises:
        FileNotFoundError: If file couldn't be located.
    """
    if not path.is_file():
        raise FileNotFoundError(f'Archive not found: {str(path)}')
    output = path.with_suffix("")
    with bz2.open(path) as fr, open(output, mode='wb') as fw:
        shutil.copyfileobj(fr, fw)  # noqa
    return output


def unpack_7z_7zip(path: Path, cmd: str = "7z") -> Path:
    """Unpack target '7z' archive using 7-Zip.

    Args:
        path: Path to the archive.
        cmd: 7-Zip command to use.

    Returns:
        Path to the directory containing extracted contents.

    Raises:
        RuntimeError: If 7-Zip encounters an exception trying to extract the archive.
    """
    output = path.parent
    proc = subprocess.run(
        [
            cmd,
            "x",
            "-y",
            "-bd",
            "-bso0",
            "-bse0",
            f"-o{str(output)}",
            str(path)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(f"7-Zip extraction failed (rc={proc.returncode}) for: {path}")
    return output


def unpack_7z_py(path: Path) -> Path:
    """Unpack target '7z' archive using py7zr.

    Args:
        path: Path to the archive.

    Returns:
        Path to the directory containing extracted contents.
    """
    output = path.parent
    with py7zr.SevenZipFile(path, 'r') as z:
        z.extractall(path=output)
    return output


# noinspection PyDeprecation
def unpack_7z(path: Path) -> Path:
    """Unpack target '7z' archive.

    Args:
        path: Path to the archive.

    Returns:
        Path to the directory containing extracted contents.

    Raises:
        FileNotFoundError: If archive couldn't be located.
    """
    if not path.is_file():
        raise FileNotFoundError(f'Archive not found: {str(path)}')
    try:
        exe = shutil.which("7z") or shutil.which("7za")
        if exe:
            return unpack_7z_7zip(path, exe)
    except (OSError, RuntimeError):
        pass
    return unpack_7z_py(path)


def unpack_tar(path: Path) -> Path:
    """Unpack a tar archive safely into its parent directory. Uses Python 3.12+'s
        built-in tar extraction filter to block unsafe paths, links, and special
        files that could escape the target directory.

    Args:
        path: Path to the archive.

    Returns:
        Path to the directory containing extracted contents.

    Raises:
        FileNotFoundError: If archive couldn't be located.
        tarfile.TarError: If the archive is invalid or extraction fails.
    """
    output = path.parent

    if not path.is_file():
        raise FileNotFoundError(f"Archive not found: {path}")
    with tarfile.open(path, "r:*") as tf:
        tf.extractall(path=output, filter="data")
    return output


def unpack_tar_7z(path: Path) -> Path:
    """Unpack target '7z' archive of tar file, then unpack tar file.

        Args:
            path: Path to the archive.

        Raises:
            FileNotFoundError: If archive couldn't be located.
        """
    _tar_file = path.with_suffix("")
    if not path.is_file():
        raise FileNotFoundError(f"Archive not found: {path}")

    unpack_7z(path)
    try:
        return unpack_tar(_tar_file)
    finally:
        if _tar_file.exists():
            _tar_file.unlink(missing_ok=True)


def unpack_archive(path: Path, remove: bool = True, thread_lock: Optional[Lock] = None) -> None | Path:
    """Unpack an archive using the correct methodology based on its extension.

    Args:
        path: Path to the archive.
        remove: Whether to remove the archive after unpacking.
        thread_lock: Optional Lock object used to prevent concurrent unpacking, will use
            default Lock object if not provided.

    Returns:
        Path to the directory of extracted contents or the extracted file. Returns None if archive doesn't exist
            or failed to extract.

    Raises:
        FileNotFoundError: If archive couldn't be located.
    """
    _lock: Lock = thread_lock or ARCHIVE_LOCK
    action_map: dict[str, Callable] = {
        ArchType.Zip: unpack_zip,
        ArchType.GZip: unpack_gz,
        ArchType.XZip: unpack_xz,
        ArchType.BZip2: unpack_bz2,
        ArchType.Tar: unpack_tar,
        ArchType.TarGZip: unpack_tar,
        ArchType.TarXZip: unpack_tar,
        ArchType.TarBZip2: unpack_tar,
        ArchType.TarSevenZip: unpack_tar_7z,
        ArchType.SevenZip: unpack_7z
    }

    # Determine the unpacking action
    archive_type = _archive_type(path)
    if archive_type is None:
        return None
    action = action_map[archive_type]

    # Unpack the archive and garbage collect
    with _lock:
        output = action(path)
        if remove:
            path.unlink(missing_ok=True)
        # * Note: Many sequential calls to this func can result
        #   in memory leak without manual garbage collection.
        gc.collect()
    return output
