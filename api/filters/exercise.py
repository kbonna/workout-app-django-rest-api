from django_filters import rest_framework as filters
from api.models import Exercise
from api.filters.custom_filters import IntegerFilter


def filter_limit(queryset, name, value):
    """Limit search to specified number of entries."""
    return queryset[:value]


class ExerciseFilter(filters.FilterSet):

    user__eq = IntegerFilter(field_name="owner")
    user__neq = IntegerFilter(field_name="owner", exclude=True)
    orderby = filters.OrderingFilter(fields=("name", "kind", "owner", "forks_count"))
    limit = IntegerFilter(method=filter_limit)

    class Meta:
        model = Exercise
        fields = ["user__eq", "user__neq", "orderby", "limit"]
