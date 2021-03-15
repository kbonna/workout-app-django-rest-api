import tempfile
from PIL import Image

# Endpoints names
USER_LIST_URLPATTERN_NAME = "user-list"
USER_DETAIL_URLPATTERN_NAME = "user-detail"
PASSWORD_RESET_URLPATTERN_NAME = "password-reset"
EMAIL_RESET_URLPATTERN_NAME = "email-reset"
PROFILE_PICTURE_URLPATTERN_NAME = "profile-picture"


def create_image_file(suffix=".png"):
    """Generate blank image file and return file object."""
    img = Image.new("RGB", (100, 100), (255, 0, 0))
    img_file = tempfile.NamedTemporaryFile(suffix=suffix)
    img.save(img_file)
    img_file.seek(0)
    return img_file
