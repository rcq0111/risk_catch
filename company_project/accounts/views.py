from django.shortcuts import render

# Create your views here.

import random
from rest_framework.decorators import api_view
from rest_framework.response import Response
import jwt
from django.conf import settings
from datetime import datetime, timedelta
from django.db import connection
import re

# 랜덤 6자리 중복 없는 업체 코드 생성 함수
def generate_unique_code():
    while True:
        code = f"{random.randint(0, 999999):06d}"
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM company.business WHERE code = %s", [code])
            if cursor.fetchone() is None:
                return code


@api_view(['POST']) # 이메일 중복 확인
def check_duplicate_email(request):
    email = request.data.get('email')
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM company.business WHERE email = %s", [email])
        exists = cursor.fetchone() is not None
    return Response({'duplicate': exists})

@api_view(['POST']) # 전화번호 중복 확인
def check_duplicate_phone(request):
    phone = request.data.get('phone')
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM company.business WHERE phone = %s", [phone])
        exists = cursor.fetchone() is not None
    return Response({'duplicate': exists})

@api_view(['POST'])  # 업체 등록 (회원가입)
def register_company(request):
    data = request.data
    name = data.get('name')
    manager = data.get('manager')
    email = data.get('email')
    phone = data.get('phone')

    # 유효성 검사
    if not name or len(name) > 20:
        return Response({'error': '사업명은 20자 이내여야 합니다.'}, status=400)

    if not manager or len(manager) > 10 or not re.match(r'^[가-힣a-zA-Z0-9]+$', manager):
        return Response({'error': '대표자 이름은 영어, 숫자, 한글만 허용되며 10자 이내여야 합니다.'}, status=400)

    if not re.match(EMAIL_REGEX, email):
        return Response({'error': '유효하지 않은 이메일 형식입니다.'}, status=400)

    if not re.match(PHONE_REGEX, phone):
        return Response({'error': '유효하지 않은 전화번호 형식입니다. 예: 010-1234-5678'}, status=400)

    code = generate_unique_code()

    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO company.business (name, manager, email, phone, code)
            VALUES (%s, %s, %s, %s, %s)
        """, [name, manager, email, phone, code])

    return Response({'code': code})

@api_view(['POST'])  # 6자리 업체 코드로 업체 정보 조회 (상호명, 대표자명, 이메일, 전화번호)
def find_by_code(request):
    code = request.data.get('code')
    if not code:
        return Response({'error': 'code는 필수입니다.'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name, manager, email, phone
            FROM company.business
            WHERE code = %s
        """, [code])
        row = cursor.fetchone()

    if not row:
        return Response({'error': '업체 없음'}, status=404)

    return Response({
        'name': row[0],
        'ceo_name': row[1],
        'email': row[2],
        'phone': row[3]
    })


@api_view(['GET'])  # 업체 정보를 입력하면 등록된 업체의 `업체코드`를 반환합니다.
def get_code(request):
    email = request.GET.get('email')
    phone = request.GET.get('phone')

    if not email or not phone:
        return Response({'error': 'email과 phone은 필수입니다.'}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT code
            FROM company.business
            WHERE email = %s AND phone = %s
        """, [email, phone])
        row = cursor.fetchone()

    if not row:
        return Response({'error': '해당 업체 없음'}, status=404)

    return Response({'code': row[0]})

EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'
PHONE_REGEX = r'^010-\d{4}-\d{4}$'

def get_company_id_from_token(request):
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return None
    try:
        token = auth.split(' ')[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload.get('company_id')
    except Exception:
        return None

@api_view(['PUT'])  # 업체 정보 수정
def update_business(request):
    company_id = get_company_id_from_token(request)
    if not company_id:
        return Response({'error': '인증 실패'}, status=401)

    name = request.data.get('name')
    ceo_name = request.data.get('ceo_name')
    email = request.data.get('email')
    phone = request.data.get('phone')

    update_fields = []
    values = []

    if name:
        if len(name) > 20:
            return Response({'error': '사업명은 20자 이내여야 합니다.'}, status=400)
        update_fields.append("name = %s")
        values.append(name)

    if ceo_name:
        if len(ceo_name) > 10 or not re.match(r'^[가-힣a-zA-Z0-9]+$', ceo_name):
            return Response({'error': '대표자 이름은 영어, 숫자, 한글만 허용되며 10자 이내여야 합니다.'}, status=400)
        update_fields.append("manager = %s")
        values.append(ceo_name)

    if email:
        if not re.match(EMAIL_REGEX, email):
            return Response({'error': '이메일 형식 오류'}, status=400)
        update_fields.append("email = %s")
        values.append(email)

    if phone:
        if not re.match(PHONE_REGEX, phone):
            return Response({'error': '전화번호 형식 오류'}, status=400)
        update_fields.append("phone = %s")
        values.append(phone)

    if not update_fields:
        return Response({'error': '수정할 정보 없음'}, status=400)

    values.append(company_id)
    query = f"UPDATE company.business SET {', '.join(update_fields)} WHERE idx = %s"

    with connection.cursor() as cursor:
        cursor.execute(query, values)

    return Response({'message': '수정 완료'}, status=200)


@api_view(['DELETE'])  # 업체 삭제
def delete_business(request):
    company_id = get_company_id_from_token(request)
    if not company_id:
        return Response({'error': '인증 실패'}, status=401)

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM company.business WHERE idx = %s RETURNING idx", [company_id])
        result = cursor.fetchone()

    if not result:
        return Response({'error': '삭제 대상 없음'}, status=404)

    return Response({'message': '삭제 완료'}, status=200)


@api_view(['POST'])  # 코드번호 인증 및 Access Token 발급
def signin_by_code(request):
    code = request.data.get('code')
    with connection.cursor() as cursor:
        cursor.execute("SELECT idx, code FROM company.business WHERE code = %s", [code])
        row = cursor.fetchone()

    if not row:
        return Response({'error': '업체 없음'}, status=404)

    payload = {
        'company_id': row[0],  # row[0] == idx
        'exp': datetime.utcnow() + timedelta(hours=2)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    return Response({
        'access_token': token,
        'code': row[1]  # 같이 반환
    })