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


REQUIRED_UNITS = {
    "rep": ["reps"],
    "rew": ["reps", "weight"],
    "tim": ["time"],
    "dis": ["distance"],
}

FORBIDDEN_UNITS = {
    "rep": ["weight", "time", "distance"],
    "rew": ["time", "distance"],
    "tim": ["reps", "weight", "distance"],
    "dis": ["reps", "weight", "time"],
}


def validate_exercite_units(exercise_obj, data):
    """Verify whether units passed to serialized WorkoutLogEntry match exercise type.

    Example:
        If exercise type is "rew" only "reps" and "weight" units are required. Function verify
        whethere these keys exist in data dictionary and whether they are not NULL (None). In this
        case remaining units "time" and "distance" are forbidden. Function ensures that these are
        either not present in the dictionary or their value is NULL (None).
    """
    exercise_kind = exercise_obj.kind

    # Check if required data is present and is not None
    for unit in REQUIRED_UNITS[exercise_kind]:
        if unit not in data or data[unit] is None:
            raise ValidationError({unit: f"For this exercise {unit} should be specified."})

    # Check if forbidden data is misssing or is None
    for unit in FORBIDDEN_UNITS[exercise_kind]:
        if unit in data and data[unit] is not None:
            raise ValidationError({unit: f"For this exercise {unit} should not be specified."})
