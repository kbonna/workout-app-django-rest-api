from django_filters import rest_framework as filters


class DotNotationFilterBackend(filters.DjangoFilterBackend):
    def get_filterset_kwargs(self, request, queryset, view):
        kwargs = super().get_filterset_kwargs(request, queryset, view)

        # Replace all dots in query parameter names into double underscore; this allows to use
        # dotted notation in URL querystring while it is compatible with filter field names
        data = kwargs.pop("data")
        kwargs["data"] = {
            param_name.replace(".", "__"): value for param_name, value in data.items()
        }

        return kwargs