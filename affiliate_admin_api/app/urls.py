from django.contrib import admin
from django.urls import path, include
from rest_framework import routers


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from app.views import (PaymentSummaryView, CreateEnrollmentView, EnrollmentProductDetailsView, StoreViewSet,
                       ProductViewSet, ContactViewSet, CartViewSet, ImportTaskViewSet)

router = routers.DefaultRouter()

router.register(r'stores', StoreViewSet, 'stores')
router.register(r'products', ProductViewSet, 'products')
router.register(r'contacts', ContactViewSet, 'contacts')
router.register(r'carts', CartViewSet, 'carts')
router.register(r'import-tasks', ImportTaskViewSet, 'import_csv')


urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # bulk enrollment by admin from admin panel
    path('payment-summary/', PaymentSummaryView.as_view(), name='payment_summary'),
    path('create-enrollment/', CreateEnrollmentView.as_view(), name='create_enrollment'),
    path('enrollment-product-details/', EnrollmentProductDetailsView.as_view(), name='enrollment_product_details'),
]
