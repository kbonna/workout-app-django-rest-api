def filter_limit(queryset, name, value):
    """Limit search to specified number of entries."""
    return queryset[:value]
