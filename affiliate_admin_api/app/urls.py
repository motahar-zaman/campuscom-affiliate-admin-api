from django.contrib import admin
from django.urls import path, include
from rest_framework import routers


from rest_framework_simplejwt.views import TokenRefreshView
from app.views import MyTokenObtainPairView

from app.views import (PaymentSummaryView, CreateEnrollmentView, EnrollmentProductDetailsView, StoreViewSet,
                       ProductViewSet, ContactViewSet, CartViewSet, ImportTaskViewSet, CreateEnrollmentWithPurchaserView,
                       health_check, CourseEnrollmentViewSet, StudentViewSet, RemoveEnrollmentView, SwapEnrollmentView,
                       SeatBlockReservationViewSet, SeatReservationViewSet, SeatReservationHistoryView,
                       SeatReservationTokenGenerationView, RemoveSeatRegistrationView, SwapSeatRegistrationView,
                       StoreCompanyViewSet)

router = routers.DefaultRouter()

router.register(r'stores', StoreViewSet, 'stores')
router.register(r'products', ProductViewSet, 'products')
router.register(r'contacts', ContactViewSet, 'contacts')
router.register(r'carts', CartViewSet, 'carts')
router.register(r'import-tasks', ImportTaskViewSet, 'import_csv')

router.register(r'course-enrollments', CourseEnrollmentViewSet, 'enrollments')

router.register(r'students', StudentViewSet, 'students')

# seat reservation
router.register(r'seat-block-reservations', SeatBlockReservationViewSet, 'seat_block_reservations')
router.register(r'seat-reservations', SeatReservationViewSet, 'seat_reservations')

router.register(r'store-companies', StoreCompanyViewSet, 'store_companies')


urlpatterns = [
    path('', include(router.urls)),
    path('check/', health_check),
    path('admin/', admin.site.urls),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # bulk enrollment by affiliate-admin from affiliate admin panel
    path('payment-summary/', PaymentSummaryView.as_view(), name='payment_summary'),
    path('create-enrollment/', CreateEnrollmentView.as_view(), name='create_enrollment'),
    path('create-enrollment-with-purchaser/', CreateEnrollmentWithPurchaserView.as_view(), name='create_enrollment_with_purchaser'),
    path('enrollment-product-details/', EnrollmentProductDetailsView.as_view(), name='enrollment_product_details'),

    path(r'remove-enrollment/', RemoveEnrollmentView.as_view(), name='remove_enrollment'),
    path(r'swap-enrollment/', SwapEnrollmentView.as_view(), name='swap_enrollment'),

    # seat reservation
    path(r'seat-reservation-token-generations/', SeatReservationTokenGenerationView.as_view(), name='seat_reservation_token_generations'),
    path(r'remove-seat-registration/', RemoveSeatRegistrationView.as_view(), name='remove_seat_registration'),
    path(r'swap-seat-registration/', SwapSeatRegistrationView.as_view(), name='swap_seat_registration'),
    path(r'seat-reservation-histories/', SeatReservationHistoryView.as_view(), name='seat_reservation_histories'),
]
