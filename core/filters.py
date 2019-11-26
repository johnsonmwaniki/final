
import django_filters

from core.models import Item

class CustomFilters(django_filters.FilterSet):
    class Meta:
        model=Item
        fields = ['title']