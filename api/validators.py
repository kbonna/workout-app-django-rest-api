from rest_framework.validators import ValidationError
import re
import string

youtube_regex = (
    r"(https?://)?(www\.)?"
    r"(youtube|youtu|youtube-nocookie)\.(com|be)/"
    r"(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
)
youtube_pattern = re.compile(youtube_regex)


def youtube_link(url, pattern=youtube_pattern):
    """Determine if url is a valid YouTube link."""
    if not pattern.match(url):
        raise ValidationError("Invalid YouTube link")


def only_letters_and_numbers(s):
    """Determine if string s is does not contain illegal characters."""
    character_set = string.ascii_lowercase + string.ascii_uppercase + string.digits
    if any((ch not in character_set for ch in s)):
        raise ValidationError("This can only contain letters and digits")