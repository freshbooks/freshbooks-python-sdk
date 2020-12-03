from datetime import date, datetime
from typing import Any, Optional, Union, List, Tuple

from freshbooks.builders import Builder


class FilterBuilder(Builder):
    """Builder for making filtered list queries.

    Filters can be builts with the methods:
    `equals`, `in_list`, `like`, `between`, and `boolean`,
    which can be chained together.

    ```python
    >>> from freshbooks import FilterBuilder

    >>> f = FilterBuilder()
    >>> f.like("email_like", "@freshbooks.com")
    FilterBuilder(&search[email_like]=@freshbooks.com)

    >>> f = FilterBuilder()
    >>> f.in_list("clientids", [123, 456]).boolean("active", False)
    FilterBuilder(&search[clientids][]=123&search[clientids][]=456&active=False)

    >>> f = FilterBuilder()
    >>> f.boolean("active", False).in_list("clientids", [123, 456])
    FilterBuilder(&active=False&search[clientids][]=123&search[clientids][]=456)

    >>> f = FilterBuilder()
    >>> f.between("amount", [1, 10])
    FilterBuilder(&search[amount_min]=1&search[amount_max]=10)

    >>> f = FilterBuilder()
    >>> f.between("start_date", date.today())
    FilterBuilder(&search[start_date]=2020-11-21)
    ```
    """

    def __init__(self) -> None:
        self._filters: List[Tuple[str, str, Any]] = []

    def __str__(self) -> str:
        query_string = self.build()
        return f"FilterBuilder({query_string})"

    def __repr__(self) -> str:  # pragma: no cover
        query_string = self.build()
        return f"FilterBuilder({query_string})"

    def boolean(self, field: str, value: bool) -> Builder:
        """Filters results where the field is equal to true or false.

        Example:
        `filter.boolean("active", False)` will yield the filter `&active=false`

        Args:
            field: The API response field to filter on
            value: True or False

        Returns:
            The FilterBuilder instance
        """
        self._filters.append(("bool", field, value))
        return self

    def equals(self, field: str, value: Any) -> Builder:
        """Filters results where the field is equal to the provided value.

        Example:
        `filter.equals("username", "Bob")` will yield the filter `&search[username]=Bob`

        Args:
            field: The API response field to filter on
            value: The value the field should equal

        Returns:
            The FilterBuilder instance
        """
        self._filters.append(("equals", field, value))
        return self

    def in_list(self, field: str, values: list) -> Builder:
        """Filters if the provided field matches a value in a list.

        In general, an 'in' filter will be bound to the plural form of the field.
        Eg. `userid` for an equal filter, `userids` for a list filter.

        Here we only append an 's' to the field name if it doesn't have one yet.
        This way we can be as forgiving as possible for developers by accepting:
        `filter.in_list("userid", [1, 2])` or `filter.in_list("userids", [1, 2])`.

        Of course the FreshBooks API is not 100% consistent, so there are a couple
        of unique cases that may not be handled.

        Args:
            field: The API response field to filter on
            values: List of values the field should one of

        Returns:
            The FilterBuilder instance
        """
        if field[-1] != "s":
            field = f"{field}s"
        self._filters.append(("in", field, values))
        return self

    def like(self, field: str, value: Any) -> Builder:
        """Filters for a match contained within the field being searched. For example,
        "leaf" will Like-match "aleaf" and "leafy", but not "leav", and "leafs" would
        not Like-match "leaf".

        Args:
            field: The API response field to filter on
            value: The value the field should contain

        Returns:
            The FilterBuilder instance
        """
        self._filters.append(("like", field, value))
        return self

    def between(self, field: str, min: Optional[Any] = None, max: Optional[Any] = None) -> Builder:
        """Filters results where the provided field is between two values.

        In general 'between' filters end in a `_min` or `_max` (as in `amount_min` or `amount_max`)
        or `_date` (as in `start_date`, `end_date`). If the provided field does not end in
        `_min`/`_max` or `_date`, then the appropriate `_min`/`_max` will be appended.

        For date fields, you can pass the iso format `2020-10-17` or a `datetime` or `date` object, which
        will be converted to the proper string format.

        Examples:

        - `filter.between("amount", 1, 10)` will yield filters `&search[amount_min]=1&search[amount_max]=10`
        - `filter.between("amount_min", min=1)` will yield filter `&search[amount_min]=1`
        - `filter.between("amount_max", max=10)` will yield filter `&search[amount_max]=10`
        - `filter.between("start_date", "2020-10-17")` will yield filter `&search[start_date]=2020-10-17`
        - `filter.between("start_date", datetime.date(year=2020, month=10, day=17))` will yield filter
          `&search[start_date]=2020-10-17`

        Args:
            field: The API response field to filter on
            min: (Optional) The value the field should be greater than (or equal to)
            max: (Optional) The value the field should be less than (or equal to)

        Returns:
            The FilterBuilder instance
        """
        if min:
            min_field = self._convert_between_field_name(field, "_min")
            min_value = self._convert_between_value(min)
            self._filters.append(("between", min_field, min_value))
        if max:
            max_field = self._convert_between_field_name(field, "_max")
            max_value = self._convert_between_value(max)
            self._filters.append(("between", max_field, max_value))
        return self

    def _convert_between_field_name(self, field: str, min_max: str) -> str:
        if field[-4:] not in ["_min", "_max"] and field[-5:] != "_date":
            return f"{field}{min_max}"
        return field

    def _convert_between_value(self, value: Union[str, Any]) -> str:
        if isinstance(value, datetime):
            return value.date().isoformat()
        elif isinstance(value, date):
            return value.isoformat()
        return value

    def build(self) -> str:
        """Builds the query string parameters from the FilterBuilder.

        Returns:
            The built query string
        """
        query_string = ""
        for filter_type, field, value in self._filters:
            if filter_type in ["equals", "like", "between"]:
                query_string = f"{query_string}&search[{field}]={value}"
            if filter_type == "in":
                for val in value:
                    query_string = f"{query_string}&search[{field}][]={val}"
            if filter_type == "bool":
                query_string = f"{query_string}&{field}={value}"
        return query_string
