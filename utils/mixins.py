from rest_framework.response import Response
from rest_framework import status


class PostMixin:
    def post(self, request, format=None):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)


class GetWithFilteringMixin:
    """

    In order for this mixin to work correctly on GenericViewSet instance one must provide custom
    method get_filtering_kwargs which return dictionary with keys:
        order_by_options:
            List of order by strings accepted as querystring search.
        prefetch_related:
            List of prefetched model fields used to avoid unnecessary db queries.
    """

    def get(self, request, format=None):
        """Return a list of all model instances.

        Querystring params:
            ?user.eq=<int>:
                Instances for user with specific pk.
            ?user.neq=<int>:
                Instances which are not owned by user with this pk.
            ?orderby=<str>:
                Name of db column to order queryset. Default order is given by pk values. Django
                convention is used – the negative sign in front of column name indicates descending
                order.
            ?limit=<int>:
                Limit querysearch to specific number of records.
        """
        user_pk_filter = request.query_params.get("user.eq", None)
        user_pk_exclude = request.query_params.get("user.neq", None)
        order_by_field = request.query_params.get("orderby", None)
        limit = request.query_params.get("limit", None)

        # Validation
        if user_pk_filter is not None and not user_pk_filter.isdigit():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if user_pk_exclude is not None and not user_pk_exclude.isdigit():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if limit is not None and not limit.isdigit():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if (
            order_by_field is not None
            and order_by_field not in self.get_filtering_kwargs()["order_by_options"]
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Use prefetch_related to reduce number of queries
        queryset = self.get_queryset()
        queryset.prefetch_related(*self.get_filtering_kwargs()["prefetch_related"])

        if user_pk_filter:
            queryset = queryset.filter(owner=user_pk_filter)
        if user_pk_exclude:
            queryset = queryset.exclude(owner=user_pk_exclude)
        if order_by_field:
            queryset = queryset.order_by(order_by_field)
        if limit:
            queryset = queryset[: int(limit)]

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(queryset, context={"request": request}, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
