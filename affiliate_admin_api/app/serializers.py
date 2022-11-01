from rest_framework import serializers

from shared_models.models import (Store, StoreConfiguration, Product, Profile, ImportTask, CourseProvider, Permission,
                                  CustomRole, CourseEnrollment, Course, Section, CartItem, ProfileCommunicationMedium,
                                  ProfileLink, IdentityProvider, ProfilePreference, SeatBlockReservation,
                                  SeatReservation, StoreCompany, SeatReservationHistory)

from django_scopes import scopes_disabled


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'name', 'action', 'operation', 'group')


class CustomRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomRole
        fields = ('id', 'name', 'permissions', 'menu_permissions')


class GetStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'name', 'url_slug', 'is_active', 'store_logo_uri', 'template')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class CartStoreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Store
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        store_configurations = StoreConfiguration.objects.filter(store=instance)
        data['configurations'] = []

        for store_config in store_configurations:
            config = {}

            config['entity_name'] = store_config.external_entity.entity_name
            config['entity_type'] = store_config.external_entity.entity_type
            config['config_value'] = store_config.config_value

            data['configurations'].append(config)

        return data


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id', 'store', 'external_id', 'product_type', 'title', 'content', 'image', 'limit_applicable',
            'total_quantity', 'quantity_sold', 'available_quantity', 'tax_code', 'fee', 'currency_code', 'ref_id',
            'minimum_fee', 'active_status'
        )
        depth = 1


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id', 'first_name', 'last_name', 'date_of_birth', 'profile_picture_uri',
                  'primary_email', 'primary_contact_number', 'terms_accepted')


class ImportTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportTask
        fields = (
            'id', 'ref_id', 'course_provider', 'store', 'import_type', 'filename', 'status', 'status_message',
            'queue_processed'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        course_provider_id = instance.course_provider.id if instance.course_provider else None
        try:
            course_provider = CourseProvider.objects.get(pk=course_provider_id)
        except CourseProvider.DoesNotExist:
            pass
        else:
            data['course_provider'] = {'id': str(course_provider.id), 'name': course_provider.name}

        try:
            store = Store.objects.get(pk=instance.store.id if instance.store else None)
        except Store.DoesNotExist:
            pass
        else:
            data['store'] = {'id': str(store.id), 'name': store.name}
        return data


class CreateImportTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportTask
        fields = (
            'id', 'course_provider', 'store', 'import_type', 'filename', 'status', 'status_message', 'queue_processed'
        )


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = ('id', 'profile', 'course', 'section', 'enrollment_time', 'application_time',
                  'status', 'store', 'cart_item', 'expiry_date', 'ref_id')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['profile'] = ProfileSerializer(Profile.objects.get(id=data['profile'])).data
        with scopes_disabled():
            data['course'] = GetCourseDetailSerializer(Course.objects.get(id=data['course'])).data
            try:
                data['section'] = GetSectionSerializer(Section.objects.get(id=data['section'])).data
            except Section.DoesNotExist:
                data['section'] = None
            try:
                data['product_id'] = str(CartItem.objects.get(id=data['cart_item']).product.id)
            except CartItem.DoesNotExist:
                data['product_id'] = None

        data['store'] = GetStoreNameIdSerializer(Store.objects.get(id=data['store'])).data

        return data


class GetCourseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id', 'title')


class GetSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ('id', 'course', 'name', 'fee', 'seat_capacity', 'available_seat',
                  'execution_mode', 'registration_deadline', 'content_db_reference', 'is_active', 'active_status')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        with scopes_disabled():
            data['course'] = GetCourseDetailSerializer(
                Course.objects.get(id=data['course'])).data
        return data


class GetStoreNameIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'name')


class ProfileCommunicationMediumSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileCommunicationMedium
        fields = ('id', 'medium_type', 'medium_value')


class ProfileLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileLink
        fields = ('id', 'identity_provider', 'provider_profile_identity')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['identity_provider'] = ProfileIdentityProviderSerializer(
            IdentityProvider.objects.get(id=data['identity_provider'])).data
        data['name'] = data['identity_provider']['name']
        del data['identity_provider']
        return data


class ProfileIdentityProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityProvider
        fields = ('id', 'name', 'slug')


class ProfilePreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePreference
        fields = ('id', 'preference_type', 'preference_value')


class ProfileEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseEnrollment
        fields = (
            'id', 'profile', 'course', 'section', 'enrollment_time', 'application_time', 'status', 'expiry_date',\
            'ref_id'
        )

class SeatBlockReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatBlockReservation
        fields = ('id', 'cart_item', 'company', 'number_of_seats', 'reservation_date', 'expiration_date', 'token_type',
                  'reservation_ref')

    def to_representation(self, instance):
        data = super().to_representation(instance)

        seat_reservation = SeatReservation.objects.filter(reservation=instance.id)
        if data['token_type'] == 'group':
            data['token'] = seat_reservation.first().token
        data['registered_students'] = seat_reservation.filter(profile__isnull=False).count()
        data['available_seats'] = data['number_of_seats'] - data['registered_students']

        try:
            company = StoreCompany.objects.get(pk=data['company'])
        except StoreCompany.DoesNotExist:
            pass
        else:
            data['company'] = {
                'id': str(company.id),
                'name': company.company_name,
            }
        with scopes_disabled():
            try:
                cart_item = CartItem.objects.get(pk=data['cart_item'])
            except CartItem.DoesNotExist:
                pass
            else:
                data['cart'] = {
                    'id': str(cart_item.cart.id),
                    'order_ref': cart_item.cart.order_ref,
                }
                data['product'] = {
                    'id': str(cart_item.product.id),
                    'name': cart_item.product.title
                }
                data['cart_item'] = {
                    'id': str(cart_item.id),
                    'quantity': cart_item.quantity,
                    'unit_price': cart_item.unit_price,
                    'extended_amount': cart_item.extended_amount,
                    'discount_amount': cart_item.discount_amount,
                    'sales_tax': cart_item.sales_tax,
                    'total_amount': cart_item.total_amount,
                    'unit': cart_item.unit
                }
                data['store'] = {
                    'id': str(cart_item.cart.store.id),
                    'url_slug': cart_item.cart.store.url_slug,
                    'name': cart_item.cart.store.name
                }
                data['purchaser'] = {
                    'id': str(cart_item.cart.profile.id),
                    'name': cart_item.cart.profile.first_name + ' ' + cart_item.cart.profile.last_name
                }
        return data


class SeatReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatReservation
        fields = ('id', 'reservation', 'profile', 'token')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            reservation = SeatBlockReservation.objects.get(pk=data['reservation'])
        except SeatBlockReservation.DoesNotExist:
            pass
        else:
            data['reservation'] = {
                'id': str(reservation.id),
                'reservation_ref': reservation.reservation_ref,
            }
        # with scopes_disabled():
        try:
            profile = Profile.objects.get(pk=data['profile'])
        except Profile.DoesNotExist:
            pass
        else:
            data['profile'] = {
                'id': str(profile.id),
                'email': profile.primary_email,
                'name': profile.first_name + ' ' + profile.last_name
            }

        try:
            enrollment = CourseEnrollment.objects.get(cart_item__seat=data['id'], active_status=True)
        except CourseEnrollment.DoesNotExist:
            pass
        else:
            data['enrollment'] = {
                'id': str(enrollment.id),
                'ref_id': enrollment.ref_id
            }

        return data


class SeatReservationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SeatReservationHistory
        fields = ('id', 'seat', 'profile', 'action', 'time')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            seat = SeatReservation.objects.get(pk=data['seat'])
        except SeatReservation.DoesNotExist:
            pass
        else:
            data['seat'] = {
                'id': str(seat.id),
                'token': seat.token,
            }
        try:
            profile = Profile.objects.get(pk=data['profile'])
        except Profile.DoesNotExist:
            pass
        else:
            data['profile'] = {
                'id': str(profile.id),
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'primary_email': profile.primary_email,
            }

        return data


class StoreCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreCompany
        fields = ('id', 'store', 'company_name')

    def to_representation(self, instance):
        data = super().to_representation(instance)

        data['store'] = None

        try:
            store_info = Store.objects.get(pk=instance.store_id)
        except Store.DoesNotExist:
            pass
        else:
            data['store'] = {'id': str(store_info.id), 'name': store_info.name}

        return data