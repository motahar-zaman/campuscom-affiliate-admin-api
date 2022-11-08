from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from campuslibs.shared_utils.data_decorators import ViewDataMixin
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin
from rest_framework.views import APIView
from rest_framework.response import Response

from shared_models.models import Store, Profile, ProfileStore
import json

from campuslibs.enrollment.common import Common


class CreateBulkEnrollmentView(APIView, SharedMixin, ViewDataMixin):
    http_method_names = ["head", "post"]

    def post(self, request, *args, **kwargs):
        enroll = Common()

        # special cases: (why not use shared_lib's common method)
        # 1. organization data will not provide as purchasing_for in purchaser_info, it will always be company and the
        # company will be from user context
        # 2. purchaser will be logged-in user or in purchaser_info

        status, message, data = self.validate_and_format_enrollment_payload(request)
        if not status:
            return Response({'message': message}, status=HTTP_400_BAD_REQUEST)

        data['admin'] = True
        status, message, processed_data = enroll.create_enrollment(data)

        if not status:
            product = {
                'id': processed_data.id,
                'title': processed_data.title
            }
            return Response({'message': message, 'product': product}, status=HTTP_400_BAD_REQUEST)

        else:
            discount = processed_data.pop('data')
            processed_data.pop('date_time')
            processed_data.update(discount)

        return Response(self.object_decorator(processed_data), status=HTTP_200_OK)

    def validate_and_format_enrollment_payload(self, request):
        data = {}

        files = request.FILES.getlist('files', None)
        token_id = request.data.get('tid', None)
        zip_code = request.data.get('zip_code', None)
        country = request.data.get('country', None)
        nonce = request.data.get('nonce', None)
        payment_ref = request.data.get('payment_ref', None)
        payment_note = request.data.get('payment_note', None)
        store_payment_gateway_id = request.data.get('store_payment_gateway_id', None)
        seat_reservation_id = request.data.get('seat_reservation', None)

        agreement_details = request.data.get('agreement_details', {})
        if agreement_details:
            agreement_details = json.loads(agreement_details)

        registration_details = request.data.get('registration_details', {})
        if registration_details:
            registration_details = json.loads(registration_details)

        coupon_codes = request.data.get('coupon_codes', [])
        if coupon_codes:
            coupon_codes = json.loads(coupon_codes)

        cart_details = request.data.get('cart_details', [])
        if cart_details:
            cart_details = json.loads(cart_details)

        purchaser_info = request.data.get('purchaser_info', {})
        if purchaser_info:
            purchaser_info = json.loads(purchaser_info)

        if not purchaser_info or not purchaser_info.get('primary_email', None):
            purchaser_info['first_name'] = request.user.first_name
            purchaser_info['last_name'] = request.user.last_name
            purchaser_info['primary_email'] = request.user.email

        purchaser_info['purchasing_for'] = {
            'type': 'company',
            'ref': request.user.db_context['Company'][0] if request.user.db_context['Company'] else None
        }

        store_id = request.data.get('store', None)
        try:
            store = Store.objects.get(pk=store_id)
        except Store.DoesNotExist:
            return False, 'Store does not exist', data

        student_details = request.data.get('student_details', [])
        if student_details:
            student_details = json.loads(student_details)
            for student in student_details:
                primary_email = student.get('email', None)
                data = {
                    'first_name': student.get('first_name', None),
                    'last_name': student.get('last_name', None)
                }
                try:
                    profile, created = Profile.objects.update_or_create(
                        primary_email=primary_email,
                        defaults=data
                    )
                except Exception as e:
                    pass
                else:
                    try:
                        profile_store = ProfileStore.objects.get_or_create(profile=profile, store=store)
                    except Exception as e:
                        pass

        data['files'] = files
        data['token_id'] = token_id
        data['student_details'] = student_details
        data['agreement_details'] = agreement_details
        data['registration_details'] = registration_details
        data['purchaser_info'] = purchaser_info
        data['store_slug'] = store.url_slug
        data['store_payment_gateway_id'] = store_payment_gateway_id
        data['payment_ref'] = payment_ref
        data['payment_note'] = payment_note
        data['coupon_codes'] = coupon_codes
        data['zip_code'] = zip_code
        data['country'] = country
        data['nonce'] = nonce
        data['cart_details'] = cart_details
        data['seat_reservation_id'] = seat_reservation_id

        return True, 'okay', data
