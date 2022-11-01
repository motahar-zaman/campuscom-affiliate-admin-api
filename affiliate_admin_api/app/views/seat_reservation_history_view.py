from rest_framework.views import APIView
from rest_framework.response import Response
from campuslibs.shared_utils.shared_function import PaginatorMixin

from rest_framework.status import HTTP_200_OK
from shared_models.models import SeatReservationHistory
from app.serializers import SeatReservationHistorySerializer


class SeatReservationHistoryView(APIView, PaginatorMixin):
    model = SeatReservationHistory
    serializer_class = SeatReservationHistorySerializer
    http_method_names = ["head", "get"]


    def get_queryset(self):
        fields = self.request.GET.copy()
        try:
            fields.pop("limit")
            fields.pop("page")
        except KeyError:
            pass

        return self.model.objects.filter(**fields.dict())

    def get(self, request, *args, **kwargs):
        histories = self.get_queryset()
        serializer = SeatReservationHistorySerializer(histories, many=True)

        return Response(self.paginate(serializer.data), status=HTTP_200_OK)

