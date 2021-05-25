from django_filters import rest_framework as filters
from api.filters.utils import (
    IntegerFilter,
    MapQueryParamNameWidget,
    PositiveIntegerFilter,
    filter_limit,
)
from api.models import Workout

map_widget = MapQueryParamNameWidget(mapping={".": "__"})


class WorkoutFilter(filters.FilterSet):

    user__eq = IntegerFilter(field_name="owner", widget=map_widget)
    user__neq = IntegerFilter(field_name="owner", exclude=True, widget=map_widget)
    orderby = filters.OrderingFilter(fields=(("date", "date")))
    limit = PositiveIntegerFilter(method=filter_limit)
    routine = IntegerFilter(field_name="routine")
    exercise = IntegerFilter(field_name="exercises")
    completed = filters.BooleanFilter()
    date__eq = filters.DateFilter(field_name="date", lookup_expr="exact", widget=map_widget)
    date__gt = filters.DateFilter(field_name="date", lookup_expr="gt", widget=map_widget)
    date__gte = filters.DateFilter(field_name="date", lookup_expr="gte", widget=map_widget)
    date__lt = filters.DateFilter(field_name="date", lookup_expr="lt", widget=map_widget)
    date__lte = filters.DateFilter(field_name="date", lookup_expr="lte", widget=map_widget)

    class Meta:
        model = Workout
        fields = [
            "user__eq",
            "user__neq",
            "orderby",
            "limit",
            "completed",
            "exercise",
            "routine",
            "date__eq",
            "date__gt",
            "date__gte",
            "date__lt",
            "date__lte",
        ]
