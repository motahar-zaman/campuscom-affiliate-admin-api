from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from campuslibs.shared_utils.data_decorators import ViewDataMixin
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin
from rest_framework.views import APIView
from rest_framework.response import Response

from shared_models.models import Store, Profile
import json

from campuslibs.enrollment.common import Common


class CreateEnrollmentWithPurchaserView(APIView, SharedMixin, ViewDataMixin):
    http_method_names = ["head", "post"]

    def post(self, request, *args, **kwargs):
        status, message, data = self.validate_and_format_payload(request)
        if not status:
            return Response({'message': message}, status=HTTP_400_BAD_REQUEST)

        enroll = Common()
        status, message, processed_data = enroll.create_enrollment(data)
        if not status:
            return Response({'message': message}, status=HTTP_400_BAD_REQUEST)
        else:
            discount = processed_data.pop('data')
            processed_data.pop('date_time')
            processed_data.update(discount)
            return Response(self.object_decorator(processed_data), status=HTTP_200_OK)

    def validate_and_format_payload(self, request):
        data = {}

        files = request.FILES.getlist('files', None)
        token_id = request.data.get('tid', None)
        zip_code = request.data.get('zip_code', None)
        country = request.data.get('country', None)
        nonce = request.data.get('nonce', None)
        store_id = request.data.get('store', None)
        payment_ref = request.data.get('payment_ref', None)
        payment_note = request.data.get('payment_note', None)
        store_payment_gateway_id = request.data.get('store_payment_gateway_id', None)
        purchaser_info = json.loads(request.data.get('purchaser_info', {}))

        if not purchaser_info:
            return False, 'Purchaser information must be provided', data

        try:
            store = Store.objects.get(pk=store_id)
        except Store.DoesNotExist:
            return False, 'Store does not exist', data

        student_details = request.data.get('student_details', [])
        if student_details:
            student_details = json.loads(student_details)
            for idx, student in enumerate(student_details):
                try:
                    profile = Profile.objects.get(pk=student.get('profile_id', None))
                except Profile.DoesNotExist:
                    return False, 'Student with this profile id not found', data
                else:
                    student_details[idx]['first_name'] = profile.first_name
                    student_details[idx]['last_name'] = profile.last_name
                    student_details[idx]['email'] = profile.primary_email

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
        data['admin'] = True

        return True, 'okay', data
