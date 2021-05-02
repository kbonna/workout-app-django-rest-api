from django import forms
from django.http import QueryDict


class MapQueryParamNameWidget(forms.Widget):
    """Convert query parameter names using mapping dictionary. This can be used if your query
    parameter names contains characters that are not allowed in valid Python variables i.e. dots.

    Args:
        mapping (dict):
            Mapping used in string replace method. For example mapping = {".", "__"} would turn
            query parameter name "age.gt" into "age__gt".
    """

    def __init__(self, mapping):
        super().__init__()
        if not isinstance(mapping, dict):
            raise TypeError("mapping should be a dict")
        self.mapping = mapping

    def value_from_datadict(self, data, files, name):
        mapped_data = dict()
        for param, value in data.items():
            for k, v in self.mapping.items():
                param = param.replace(k, v)
            mapped_data[param] = value

        # turn dict back into QueryDict
        data = QueryDict("", mutable=True)
        data.update(mapped_data)
        return super().value_from_datadict(data, files, name)
