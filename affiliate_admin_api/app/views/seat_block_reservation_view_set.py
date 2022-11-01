from shared_models.models import SeatBlockReservation
from rest_framework import viewsets
from campuslibs.shared_utils.shared_function import PaginatorMixin

from campuslibs.shared_utils.data_decorators import ViewDataMixin
from rest_framework.response import Response

from rest_framework.status import HTTP_200_OK

from app.serializers import SeatBlockReservationSerializer


class SeatBlockReservationViewSet(viewsets.ModelViewSet, ViewDataMixin, PaginatorMixin):
    """
    A viewset for viewing and editing SeatBlockReservation.
    """
    serializer_class = SeatBlockReservationSerializer
    http_method_names = ["get", "head"]
    model = SeatBlockReservation

    def get_queryset(self):
        fields = self.request.GET.copy()
        try:
            fields.pop("limit")
            fields.pop("page")
        except KeyError:
            pass

        return self.model.objects.filter(**fields.dict())

    def retrieve(self, request, *args, **kwargs):
        reservation = self.get_object()
        serializer = self.serializer_class(reservation)
        return Response(self.object_decorator(serializer.data), status=HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(self.paginate(serializer.data), status=HTTP_200_OK)
