from django.urls import path
from . import views

urlpatterns = [
    path('duplicate/email', views.check_duplicate_email), # 이메일 중복 확인
    path('duplicate/phone', views.check_duplicate_phone), # 전화번호 중복 확인
    path('signup', views.register_company),  # 기존 register_company 재사용 / 업체 등록 API
    path('signin', views.signin_by_code),    # JWT 발급 / 코드번호 인증 및 Access Token 발급
    path('find-by-code/', views.find_by_code), # 코드로 업체 조회
    path('update/', views.update_business),   # PUT /api/accounts/update/
    path('delete/', views.delete_business),   # DELETE /api/accounts/delete/
    path('get-code/', views.get_code), # 업체 정보를 입력하면 등록된 업체의 `업체코드`를 반환합니다.
]
