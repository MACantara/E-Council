"""Shared WTForms validators and helpers for E-Council."""

from wtforms.validators import ValidationError


def coerce_int(value):
    """Coerce form value to int, treating empty/None as None."""
    if value is None or value == '' or value == 'None':
        return None
    return int(value)


def coerce_float(value):
    """Coerce form value to float, treating empty/None as None."""
    if value is None or value == '' or value == 'None':
        return None
    return float(value)


class PasswordStrength:
    """Validate that a password meets the E-Council policy."""

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        password = field.data or ''

        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters.')
        if not any(char.isupper() for char in password):
            raise ValidationError('Password must contain at least one uppercase letter.')
        if not any(char.islower() for char in password):
            raise ValidationError('Password must contain at least one lowercase letter.')
        if not any(char.isdigit() for char in password):
            raise ValidationError('Password must contain at least one number.')
        if not any(char in '!@#$%^&*(),.?":{}|<>' for char in password):
            raise ValidationError('Password must contain at least one special character.')
