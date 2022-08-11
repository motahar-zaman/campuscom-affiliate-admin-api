from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from django.conf import settings
from shared_models.models import Course


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# from app.views import (PaymentSummaryView, CreateEnrollmentView, EnrollmentProductDetailsView)

router = routers.DefaultRouter()


urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # bulk enrollment by admin from admin panel
    # path('payment-summary/', PaymentSummaryView.as_view(), name='payment_summary'),
    # path('create-enrollment/', CreateEnrollmentView.as_view(), name='create_enrollment'),
    # path('enrollment-product-details/', EnrollmentProductDetailsView.as_view(), name='enrollment_product_details'),
]
