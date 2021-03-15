import hashlib
import os
from functools import partial

from django.urls import reverse
from django.utils.http import urlencode


def build_url(*args, **kwargs):
    params = kwargs.pop("params", {})
    url = reverse(*args, **kwargs)
    if params:
        url += "?" + urlencode(params)
    return url


def hash_file(file, block_size=65536):
    hasher = hashlib.md5()
    for buf in iter(partial(file.read, block_size), b""):
        hasher.update(buf)
    return hasher.hexdigest()


def hash_upload_to(field_name, base_dir=""):
    """Function to supply in upload_to field hashing file creating unique filename.

    Args:
        field_name (str):
            FileField or ImageField name.
        base_dir (str):
            Path to base directory in which files should be saved.

    Returns:
        upload_to function returning hashed filename.
    """

    def inner(instance, filename):
        filename_base, filename_ext = os.path.splitext(filename)
        file_field = instance.__getattribute__(field_name)
        new_filename = "{0}{1}".format(hash_file(file_field), filename_ext)
        return base_dir + new_filename

    return inner
