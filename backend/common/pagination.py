from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """`?page=N`, 20 per page -> {count, next, previous, results}."""

    page_size = 20
