"""
* Utils: Images
"""
from pathlib import Path
from typing import Optional

from PIL import Image
from PIL.Image import Resampling


"""
* Util Funcs
"""


def downscale_image_by_width(
    path_img: Path,
    path_save: Optional[Path] = None,
    max_width: Optional[int] = None,
    optimize: bool = True,
    quality: int | int = 95,
    resample: Resampling = Resampling.LANCZOS,
    convert_rgb: bool = True
) -> Path | None:
    """Downscale an image proportionately to a given maximum width value.

    Args:
        path_img (Path): Path to the image.
        path_save (Path): Path the downscaled image should be saved as. If not provided, will save to:
            /{parent dir}/compressed/{image name}.jpg
        max_width (int): Maximum width of the downscaled image, default: Existing width / 2
        optimize (bool): Whether to use Pillow optimize, default: True
        quality (int): Output image quality, 1-100, default: 95
        resample (Resampling): Resampling algorithm, default: LANCZOS
        convert_rgb (bool): Whether to convert image to RGB, default: True

    Raises:
        OSError: If the image couldn't be downscaled or saved.

    Returns:
        Path to the downscaled image if successful, otherwise None.
    """
    # Open the image, get dimensions
    with Image.open(path_img) as image:

        # Calculate ratio
        if max_width is None:
            max_width = image.width / 2
        ratio = max_width / image.width

    # Forward to ratio-based downscale
    return downscale_image(
        path_img=path_img,
        path_save=path_save,
        ratio=min(ratio, 100),
        optimize=optimize,
        quality=quality,
        resample=resample,
        convert_rgb=convert_rgb)


def downscale_image_by_height(
    path_img: Path,
    path_save: Optional[Path] = None,
    max_height: Optional[int] = None,
    optimize: bool = True,
    quality: int | int = 95,
    resample: Resampling = Resampling.LANCZOS,
    convert_rgb: bool = True
) -> Path | None:
    """Downscale an image proportionately to a given maximum height value.

    Args:
        path_img (Path): Path to the image.
        path_save (Path): Path the downscaled image should be saved as. If not provided, will save to:
            /{parent dir}/compressed/{image name}.jpg
        max_height (int): Maximum height of the downscaled image, default: Existing height / 2
        optimize (bool): Whether to use Pillow optimize, default: True
        quality (int): Output image quality, 1-100, default: 95
        resample (Resampling): Resampling algorithm, default: LANCZOS
        convert_rgb (bool): Whether to convert image to RGB, default: True

    Raises:
        OSError: If the image couldn't be downscaled or saved.

    Returns:
        Path to the downscaled image if successful, otherwise None.
    """
    # Open the image, get dimensions
    with Image.open(path_img) as image:

        # Calculate ratio
        if max_height is None:
            max_height = image.height / 2
        ratio = (max_height / image.height)

    # Forward to ratio-based downscale
    return downscale_image(
        path_img=path_img,
        path_save=path_save,
        ratio=min(ratio, 100),
        optimize=optimize,
        quality=quality,
        resample=resample,
        convert_rgb=convert_rgb)


def downscale_image(
    path_img: Path,
    path_save: Optional[Path] = None,
    ratio: int | float = 50,
    optimize: bool = True,
    quality: int | int = 95,
    resample: Resampling = Resampling.LANCZOS,
    convert_rgb: bool = True
) -> Path | None:
    """Downscale an image proportionately to a given size ratio.

    Args:
        path_img (Path): Path to the image.
        path_save (Path): Path the downscaled image should be saved as. If not provided, will save to:
            /{parent dir}/compressed/{image name}.jpg
        ratio (int | float): Ratio to downscale, default: 50
        optimize (bool): Whether to use Pillow optimize, default: True
        quality (int): Output image quality, 1-100, default: 95
        resample (Resampling): Resampling algorithm, default: LANCZOS
        convert_rgb (bool): Whether to convert image to RGB, default: True

    Raises:
        OSError: If the image couldn't be downscaled or saved.

    Returns:
        Path to the downscaled image if successful, otherwise None.
    """
    # Establish our source and destination directories
    if path_save is None:
        path_save = (path_img.parent / 'compressed' / path_img.name).with_suffix('.jpg')
    if not path_save.parent.is_dir():
        path_save.parent.mkdir(mode=777, parents=True, exist_ok=True)

    # Open the image, get dimensions
    with Image.open(path_img) as image:

        # Convert to RGB
        if convert_rgb:
            image.convert('RGB')

        # Downscale
        if ratio < 100:
            width, height = image.size
            image.thumbnail(
                size=(
                    round(width * ratio),
                    round(height * ratio)),
                resample=resample)

        # Save the new image
        try:
            image.save(
                fp=path_save,
                quality=quality,
                optimize=optimize)
        except (FileExistsError, PermissionError) as e:
            raise OSError("I don't have permission to save the downscaled image.") from e
        except Exception as e:
            raise OSError("Couldn't downscale the provided image.") from e
        return path_save
