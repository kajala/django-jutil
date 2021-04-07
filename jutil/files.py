import os
from typing import List
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from jutil.format import is_media_full_path, strip_media_root


def list_files(
    dir_name: str, suffix: str = "", ignore_case: bool = True, media_root: bool = False, recurse: bool = False
) -> List[str]:
    """
    Lists all files under specified directory.
    Optionally filter files by suffix and recurse to subdirectories.
    :param dir_name: Directory path
    :param suffix: Case-sensitive suffix (optional)
    :param ignore_case: Case-insensitive suffix. Default is True.
    :param recurse: Recurse subdirectories (optional)
    :param media_root: Instead of full path return files relative to media root.
    :return: List of file names
    """
    if not os.path.isdir(dir_name):
        raise ValidationError(_("{} is not a directory").format(dir_name))
    dir_full_path = os.path.abspath(dir_name)
    if not is_media_full_path(dir_full_path):
        raise ValidationError(_("{} is not under MEDIA_ROOT"))
    out: List[str] = []
    if suffix and ignore_case:
        suffix = suffix.lower()
    for ent in os.scandir(dir_full_path):
        assert isinstance(ent, os.DirEntry)
        if ent.is_file():
            name = ent.name
            if suffix and ignore_case:
                name = name.lower()
            if not suffix or name.endswith(suffix):
                file_path = strip_media_root(ent.path) if media_root else str(ent.path)
                out.append(file_path)
        elif recurse and ent.is_dir() and ent.name != "." and ent.name != "..":
            out.extend(
                list_files(ent.path, suffix=suffix, ignore_case=ignore_case, media_root=media_root, recurse=recurse)
            )
    return out
