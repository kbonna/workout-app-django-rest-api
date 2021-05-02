from django_filters import rest_framework as filters
from api.filters.utils import (
    IntegerFilter,
    PositiveIntegerFilter,
    MapQueryParamNameWidget,
    filter_limit,
)
from api.models import Routine

map_widget = MapQueryParamNameWidget(mapping={".": "__"})


class RoutineFilter(filters.FilterSet):

    user__eq = IntegerFilter(field_name="owner", widget=map_widget)
    user__neq = IntegerFilter(field_name="owner", exclude=True, widget=map_widget)
    orderby = filters.OrderingFilter(fields=("name", "kind", "owner", "forks_count"))
    limit = PositiveIntegerFilter(method=filter_limit)

    class Meta:
        model = Routine
        fields = ["user__eq", "user__neq", "orderby", "limit"]
