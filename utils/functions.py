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


def query_params(**d):
    """Create querystring from query parameters."""
    return "?" + "&".join(f"{k}={v}" for k, v in d.items())


def hash_file(file, block_size=65536):
    hasher = hashlib.md5()
    for buf in iter(partial(file.read, block_size), b""):
        hasher.update(buf)
    return hasher.hexdigest()


def hash_upload_to(instance, filename):
    """In case hashing filenames will be required in the future. Not working template."""
    _, filename_ext = os.path.splitext(filename)
    file_field = instance.__getattribute__("profile_picture")
    new_filename = "{0}{1}".format(hash_file(file_field), filename_ext)
    return new_filename
