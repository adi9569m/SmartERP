from decimal import Decimal, InvalidOperation


class ValidationError(ValueError):
    pass


def require(data, *fields):
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise ValidationError(f"Required fields: {', '.join(missing)}")


def money(value, field):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValidationError(f"{field} must be numeric")
    if result < 0:
        raise ValidationError(f"{field} cannot be negative")
    return result


def positive(value, field):
    result = money(value, field)
    if result <= 0:
        raise ValidationError(f"{field} must be greater than zero")
    return result
