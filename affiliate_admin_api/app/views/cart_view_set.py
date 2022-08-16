from campuslibs.shared_utils.data_decorators import ViewDataMixin
from campuslibs.shared_utils.shared_function import PaginatorMixin, SharedMixin
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django_scopes import scopes_disabled
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from shared_models.models import (
    Cart,
    StoreCourseSection,
    StoreCertificate,
    QuestionBank,
    RelatedProduct,
    RelatedProductPurchase,
    Profile,
    StoreCompany,
)


class CartViewSet(viewsets.ModelViewSet, PaginatorMixin, SharedMixin, ViewDataMixin):
    """
    A viewset for viewing and editing catalog.
    """

    model = Cart
    http_method_names = ["get", "head"]

    def get_queryset(self):
        fields = self.request.GET.copy()

        if "product_type" in fields.keys():
            fields.pop("product_type")

        if "created_at__lte" in fields.keys():
            to_date = datetime.strptime(fields["created_at__lte"], "%Y-%m-%d")
            to_date = to_date + timedelta(days=1)
            fields["created_at__lte"] = to_date.strftime("%Y-%m-%d")

        try:
            fields.pop("limit")
            fields.pop("page")
        except KeyError:
            pass

        return self.get_scoped_queryset(fields=fields)

    def retrieve(self, request, *args, **kwargs):
        cart = self.get_object()
        item = cart.cart_items.first()

        profile = {}
        if cart.profile is not None:
            profile = {
                "id": str(cart.profile.id),
                "first_name": cart.profile.first_name,
                "last_name": cart.profile.last_name,
                "primary_email": cart.profile.primary_email,
            }

        for idx, student_details in enumerate(cart.student_details):
            extra_info = []
            if "extra_info" in student_details:
                for qbank_id, answer in student_details["extra_info"].items():
                    try:
                        qbank = QuestionBank.objects.get(id=qbank_id)
                    except (QuestionBank.DoesNotExist, ValidationError):
                        pass
                    else:
                        extra_info.append(
                            {
                                "id": str(qbank.id),
                                "title": qbank.title,
                                "type": qbank.question_type,
                                "answer": answer,
                            }
                        )
                cart.student_details[idx]["extra_info"] = extra_info

        for idx, reg_data in enumerate(cart.registration_details):
            registration_details_data = []
            if "data" in reg_data:
                for qbank_id, answer in reg_data["data"].items():
                    try:
                        qbank = QuestionBank.objects.get(id=qbank_id)
                    except (QuestionBank.DoesNotExist, ValidationError):
                        pass
                    else:
                        registration_details_data.append(
                            {
                                "id": str(qbank.id),
                                "title": qbank.title,
                                "type": qbank.question_type,
                                "answer": answer,
                            }
                        )
                cart.registration_details[idx]["data"] = registration_details_data

        agreement_details_data = []
        for qbank_id, answer in cart.agreement_details.items():
            try:
                qbank = QuestionBank.objects.get(id=qbank_id)
            except (QuestionBank.DoesNotExist, ValidationError):
                pass
            else:
                agreement_details_data.append(
                    {
                        "id": str(qbank.id),
                        "title": qbank.title,
                        "type": qbank.question_type,
                        "answer": answer,
                    }
                )

        extra_info = []
        if "extra_info" in cart.purchaser_info:
            for qbank_id, answer in cart.purchaser_info["extra_info"].items():
                try:
                    qbank = QuestionBank.objects.get(id=qbank_id)
                except (QuestionBank.DoesNotExist, ValidationError):
                    pass
                else:
                    extra_info.append(
                        {
                            "id": str(qbank.id),
                            "title": qbank.title,
                            "type": qbank.question_type,
                            "answer": answer,
                        }
                    )
            cart.purchaser_info["extra_info"] = extra_info

        # Purchasing for info modified if for company
        purchasing_for = cart.purchaser_info.get('purchasing_for', None)
        if purchasing_for and purchasing_for['type'] == 'company':
            company_id = purchasing_for.get('ref', None)
            if company_id:
                try:
                    company = StoreCompany.objects.get(pk=company_id)
                except StoreCompany.DoesNotExist:
                    pass
                else:
                    cart.purchaser_info['purchasing_for']['ref'] = {
                        'id': company_id,
                        'company_name': company.company_name
                    }

        cart_details = []
        for item in cart.cart_items.all():
            students = []
            rel_product_purchases = RelatedProductPurchase.objects.filter(
                related_product__related_product=item.product, cart=cart
            )
            for purchase in rel_product_purchases:
                try:
                    student_profile = Profile.objects.get(
                        primary_email=purchase.student_email
                    )
                except (Profile.DoesNotExist, Profile.MultipleObjectsReturned):
                    name = ""
                else:
                    name = f"{student_profile.first_name} {student_profile.last_name}"
                students.append(
                    {
                        "name": name,
                        "email": purchase.student_email,
                        "quantity": purchase.quantity,
                    }
                )

            related_products = RelatedProduct.objects.filter(
                related_product=item.product
            )
            if related_products.exists():
                related_product_type = related_products.first().related_product_type
            else:
                related_product_type = None

            cart_details.append(
                {
                    "id": str(item.id),
                    "product_id": str(item.product.id),
                    "ref_id": str(item.product.ref_id),
                    "product_name": item.product.title,
                    "parent_product_name": item.parent_product.title
                    if item.parent_product
                    else None,
                    "related_product_type": related_product_type,
                    "unit_price": item.unit_price,
                    "quantity": item.quantity,
                    "extended_amount": item.extended_amount,
                    "discount": item.discount_amount,
                    "total_amount": item.total_amount,
                    "sales_tax": item.sales_tax,
                    "students": students,
                }
            )

        cart.agreement_details = agreement_details_data
        req_data = {}
        resp_data = {}
        if cart.enrollment_request is not None:
            req_data = cart.enrollment_request.get("request", {})
            resp_data = cart.enrollment_request.get("response", {})
            notification_request = cart.enrollment_request.get(
                "enrollment_notification", {}
            )
            notification_response = cart.enrollment_request.get(
                "enrollment_notification_response", {}
            )

        data = {
            "id": str(cart.id),
            "order_ref": cart.order_ref,
            "store": {"id": str(cart.store.id), "name": cart.store.name},
            "profile": profile,
            "datetime": cart.created_at,
            "cart_status": cart.status,
            "gross_amount": cart.gross_amount,
            "total_discount": cart.total_discount,
            "tax_amount": cart.sales_tax,
            "total_amount": cart.total_amount,
            "registration_details": cart.registration_details,
            "agreement_details": cart.agreement_details,
            # these fields will be removed
            "purchaser_info": cart.purchaser_info,
            "student_details": cart.student_details,
            "enrollment_request": req_data,
            "enrollment_response": resp_data,
            "enrollment_notification": notification_request,
            "enrollment_notification_response": notification_response,
            "cart_details": cart_details,
        }

        try:
            with scopes_disabled():
                store_course_section = StoreCourseSection.objects.get(
                    product=item.product
                )
        except StoreCourseSection.DoesNotExist:
            pass
        else:
            data["product_title"] = store_course_section.store_course.course.title
            data["product_type"] = "store_course_section"

        try:
            with scopes_disabled():
                store_certificate = StoreCertificate.objects.get(product=item.product)
        except StoreCertificate.DoesNotExist:
            pass
        else:
            data["product_title"] = store_certificate.certificate.title
            data["product_type"] = "certificate"
        return Response(self.object_decorator(data), status=HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        store_id = self.request.query_params.get("store", None)
        product_type = self.request.query_params.get("product_type", None)
        status = self.request.query_params.get("status", None)

        queryset = self.get_queryset()

        if store_id is not None:
            queryset = queryset.filter(store__id=store_id)

        if status is not None:
            queryset = queryset.filter(status=status)

        data = []
        with scopes_disabled():
            for cart in queryset:
                if not cart.cart_items.exists():
                    continue

                profile = {}
                if cart.profile is not None:
                    profile = {
                        "id": str(cart.profile.id),
                        "first_name": cart.profile.first_name,
                        "last_name": cart.profile.last_name,
                        "primary_email": cart.profile.primary_email,
                    }
                product = {
                    "id": str(cart.id),
                    "ref_id": cart.order_ref,
                    "datetime": cart.created_at,
                    "profile": profile,
                    "status": cart.status,
                    "store": {"id": str(cart.store.id), "name": cart.store.name},
                    "registration_details": cart.registration_details,
                    "agreement_details": cart.agreement_details,
                    # these fields will be removed
                    "purchaser_info": cart.purchaser_info,
                    "student_details": cart.student_details,
                }

                item = cart.cart_items.first()

                if product_type == "store_course_section":
                    try:
                        store_course_section = StoreCourseSection.objects.get(
                            product=item.product
                        )
                    except StoreCourseSection.DoesNotExist:
                        continue
                    else:
                        product["product_type"] = "store_course_section"
                        product[
                            "product_title"
                        ] = store_course_section.store_course.course.title
                elif product_type == "certificate":
                    try:
                        store_certificate = StoreCertificate.objects.get(
                            product=item.product
                        )
                    except StoreCertificate.DoesNotExist:
                        continue
                    else:
                        product["product_type"] = ("certificate",)
                        product["product_title"] = store_certificate.certificate.title
                else:
                    try:
                        store_course_section = StoreCourseSection.objects.get(
                            product=item.product
                        )
                    except StoreCourseSection.DoesNotExist:
                        pass
                    else:
                        product["product_type"] = "store_course_section"
                        product[
                            "product_title"
                        ] = store_course_section.store_course.course.title

                    try:
                        store_certificate = StoreCertificate.objects.get(
                            product=item.product
                        )
                    except StoreCertificate.DoesNotExist:
                        pass
                    else:
                        product["product_type"] = "certificate"
                        product["product_title"] = store_certificate.certificate.title
                data.append(product)

        return Response(self.paginate(data), status=HTTP_200_OK)
