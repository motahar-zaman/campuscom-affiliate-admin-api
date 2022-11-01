from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response

from campuslibs.shared_utils.data_decorators import ViewDataMixin

from shared_models.models import SeatBlockReservation, SeatReservation
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST
)
import random


class SeatReservationTokenGenerationView(UpdateAPIView, ViewDataMixin):

    def update(self, request, *args, **kwargs):
        reservation_id = request.data.get('reservation_id', None)
        token_type = request.data.get('token_type', None)

        try:
            reservation = SeatBlockReservation.objects.get(pk=reservation_id)
        except SeatBlockReservation.DoesNotExist:
            return Response(
                {
                    "error": {"message": "SeatBlockReservation does not exists"},
                    "status_code": 400,
                },
                status=HTTP_400_BAD_REQUEST,
            )
        else:
            if token_type == 'individual' and reservation.token_type is not token_type:
                reservation.token_type = token_type
                reservation.save()

                seats = SeatReservation.objects.filter(reservation=reservation.id, profile__isnull=True)
                for indx, seat in enumerate(seats):
                    start = 10000000
                    end = start + seats.count() + 100
                    data = list(range(start, end))
                    random.shuffle(data)
                    seat.token = str(data[indx]) + str(reservation.reservation_ref)
                    seat.save()

        return Response({"message": "Successfully generate token for individuals"}, status=HTTP_200_OK)
