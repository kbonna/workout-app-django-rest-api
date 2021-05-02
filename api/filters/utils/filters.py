from django import forms
from django_filters.filters import Filter


class PositiveIntegerField(forms.fields.IntegerField):
    def __init__(self, *, min_value=None, max_value=None, **kwargs):
        min_value = 0 if min_value is None or min_value < 0 else min_value
        super().__init__(max_value=None, min_value=min_value, **kwargs)


class IntegerFilter(Filter):
    field_class = forms.IntegerField


class PositiveIntegerFilter(Filter):
    field_class = PositiveIntegerField
