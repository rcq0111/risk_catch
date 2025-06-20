# from django.urls import path
# from . import views
#
# urlpatterns = [
#     path('upload/', views.upload_csvs),
#     path('analyze/', views.analyze_files),
#     path('result/', views.get_result),
# ]


from django.urls import path
from .views import register_data  # views.py에 만든 함수 import
from .views import analyze_model_outputs
from .views import read_business_data

urlpatterns = [
    # POST /api/files/register/
    # - JWT 토큰에 포함된 business_idx를 사용하여
    #   제품 생산/판매 데이터를 등록하는 API
    path('register/', register_data, name='register_data'),

    path('analyze-files/', analyze_model_outputs),  # /api/files/analyze-files/
    path('read/', read_business_data),  # ✅ 데이터 조회 API
]
