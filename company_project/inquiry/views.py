from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
from django.conf import settings
import jwt


# 🔒 토큰에서 business_idx 추출

def get_business_idx(request):
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return None
    try:
        token = auth.split(' ')[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload.get('company_id')
    except:
        return None

# ✅ 1. 문의 등록
@api_view(['POST'])
def post_question(request):
    business_idx = get_business_idx(request)
    if not business_idx:
        return Response({'error': '인증 실패'}, status=401)

    data = request.data
    title = data.get('title')
    message = data.get('message')
    category_idx = data.get('category_idx')

    if not all([title, message, category_idx]):
        return Response({'error': '필수 항목 누락'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO inquiry.question (business_idx, category_idx, title, message, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, [business_idx, category_idx, title, message])

    return Response({'message': '문의 등록 완료'}, status=200)

# ✅ 2. 문의 목록 조회
@api_view(['GET'])
def get_question_list(request):
    business_idx = get_business_idx(request)
    if not business_idx:
        return Response({'error': '인증 실패'}, status=401)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT Q.idx, Q.title, Q.message, Q.created_at, Q.updated_at, C.name as category
            FROM inquiry.question Q
            JOIN inquiry.category C ON Q.category_idx = C.idx
            WHERE Q.business_idx = %s
            ORDER BY Q.created_at DESC
        """, [business_idx])
        rows = cursor.fetchall()

    results = [
        {
            'idx': row[0], 'title': row[1], 'message': row[2],
            'created_at': row[3], 'updated_at': row[4], 'category': row[5]
        } for row in rows
    ]
    return Response(results, status=200)

# ✅ 3. 문의 상세 조회
@api_view(['GET'])
def get_question_detail(request, question_idx):
    business_idx = get_business_idx(request)
    if not business_idx:
        return Response({'error': '인증 실패'}, status=401)

    with connection.cursor() as cursor:
        # 질문
        cursor.execute("""
            SELECT Q.idx, Q.title, Q.message, Q.created_at, Q.updated_at, C.name as category
            FROM inquiry.question Q
            JOIN inquiry.category C ON Q.category_idx = C.idx
            WHERE Q.idx = %s AND Q.business_idx = %s
        """, [question_idx, business_idx])
        question = cursor.fetchone()

        if not question:
            return Response({'error': '질문 없음'}, status=404)

        # 답변
        cursor.execute("""
            SELECT A.message, A.created_at, L.id AS admin_id
            FROM inquiry.answer A
            JOIN admin.list L ON A.admin_idx = L.idx
            WHERE A.question_idx = %s
            ORDER BY A.created_at ASC
        """, [question_idx])
        answers = cursor.fetchall()

    return Response({
        'question': {
            'idx': question[0], 'title': question[1], 'message': question[2],
            'created_at': question[3], 'updated_at': question[4], 'category': question[5]
        },
        'answers': [
            {'message': row[0], 'created_at': row[1], 'admin_id': row[2]} for row in answers
        ]
    }, status=200)

# ✅ 4. 카테고리 목록 조회
@api_view(['GET'])
def get_categories(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT idx, name FROM inquiry.category")
        rows = cursor.fetchall()
    return Response([{'idx': r[0], 'name': r[1]} for r in rows], status=200)
