from django_filters.filters import Filter
from django import forms


class IntegerFilter(Filter):
    field_class = forms.IntegerField