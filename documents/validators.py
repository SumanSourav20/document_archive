from django.core.validators import RegexValidator

hex_color_validator = RegexValidator(
    regex=r'^#(?:[0-9a-fA-F]{6})$',
    message="Provide a valid hex color code, e.g. #FFFFFF"
)