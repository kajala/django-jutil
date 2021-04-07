import os
from typing import List
from django.utils.translation import gettext as _
from jutil.format import is_media_full_path, strip_media_root


def list_files(
    dir_name: str, suffix: str = "", ignore_case: bool = True, use_media_root: bool = False, recurse: bool = False
) -> List[str]:
    """
    Lists all files under specified directory.
    Optionally filter files by suffix and recurse to subdirectories.
    :param dir_name: Directory path
    :param suffix: Case-sensitive suffix (optional)
    :param ignore_case: Case-insensitive suffix. Default is True.
    :param use_media_root: Instead of full path return files relative to media root.
    :param recurse: Recurse subdirectories (optional)
    :return: List of file names found
    """
    if not os.path.isdir(dir_name):
        raise ValueError(_("{} is not a directory").format(dir_name))
    dir_full_path = os.path.abspath(dir_name)
    if use_media_root and not is_media_full_path(dir_full_path):
        raise ValueError(_("{} is not under MEDIA_ROOT"))

    if suffix:
        if not suffix.startswith("."):
            suffix = "." + suffix
        if ignore_case:
            suffix = suffix.lower()

    out: List[str] = []
    for ent in os.scandir(dir_full_path):
        assert isinstance(ent, os.DirEntry)
        if ent.is_file():
            name = ent.name
            if suffix and ignore_case:
                name = name.lower()
            if not suffix or name.endswith(suffix):
                file_path = strip_media_root(ent.path) if use_media_root else os.path.abspath(ent.path)
                out.append(file_path)
        elif recurse and ent.is_dir() and ent.name != "." and ent.name != "..":
            out.extend(
                list_files(
                    ent.path, suffix=suffix, ignore_case=ignore_case, use_media_root=use_media_root, recurse=recurse
                )
            )
    return out


def find_file(filename: str, dir_name: str = ".", use_media_root: bool = False, recurse: bool = False) -> List[str]:
    """
    Finds file under specified directory.
    Optionally filter files by suffix and recurse to subdirectories.
    :param filename: File name to find. You can also specify relative paths e.g. "en/LC_MESSAGES/django.po"
    :param dir_name: Directory path. Default '.'
    :param use_media_root: Instead of full path return files relative to media root.
    :return: List of file names found
    :param recurse: Recurse subdirectories (optional)
    """
    if not os.path.isdir(dir_name):
        raise ValueError(_("{} is not a directory").format(dir_name))
    dir_full_path = os.path.abspath(dir_name)
    if use_media_root and not is_media_full_path(dir_full_path):
        raise ValueError(_("{} is not under MEDIA_ROOT"))
    out: List[str] = []
    if "/" not in filename:
        filename = "/" + filename
    for ent in os.scandir(dir_full_path):
        assert isinstance(ent, os.DirEntry)
        if ent.is_file():
            full_path = str(os.path.abspath(ent.path))
            if full_path.endswith(filename):
                file_path = strip_media_root(full_path) if use_media_root else full_path
                out.append(file_path)
        elif recurse and ent.is_dir() and ent.name != "." and ent.name != "..":
            out.extend(find_file(filename, dir_name=ent.path, use_media_root=use_media_root, recurse=recurse))
    return out
