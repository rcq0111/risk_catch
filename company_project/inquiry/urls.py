from django.urls import path
from . import views

urlpatterns = [
    path('question/', views.submit_question, name='submit-question'),                # 문의 등록
    path('question/list/', views.list_questions, name='list-questions'),             # 전체 문의 목록
    path('question/<int:idx>/', views.get_question_detail, name='question-detail'),  # 특정 문의 상세 조회
    path('categories/', views.get_categories, name='get-categories'),                # 문의 카테고리 목록
]
