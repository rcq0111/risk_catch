from django.db import connection
import pandas as pd
import io
import jwt
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .your_model_module import run_model_and_get_outputs
from .preprocessing import preprocess_csv_memory
import base64
from psycopg2.extras import execute_values  # 핵심 부분

canbin = []
@api_view(['POST'])
def register_data(request):
    try:
        # 1. JWT 토큰에서 business_idx 추출
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'error': '토큰 누락 또는 형식 오류'}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        business_idx = payload.get('company_id')
        if not business_idx:
            return Response({'error': '토큰에서 업체 정보 없음'}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.get('data')

        postData = []

        for item in data:
            postData.append((
                business_idx,
                item['type_idx'],
                item['date'],
                item['name'],
                item['number']
            ))

        query = """
            INSERT INTO data.list (business_idx, type_idx, date, name, number)
            VALUES %s
        """

        with connection.cursor() as cursor:
            execute_values(cursor, query, postData)

        return Response({'message': '등록 성공'}, status=status.HTTP_200_OK)

    except jwt.ExpiredSignatureError:
        return Response({'error': '토큰 만료'}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({'error': '유효하지 않은 토큰'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'error': '서버 내부 오류', 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# @api_view(['POST'])  # 토큰에 포함된 business_idx를 기반으로 제품 생산/판매 데이터를 서버에 등록합니다.
# def register_data(request):
#     try:
#         # 1. JWT 토큰에서 business_idx 추출
#         auth_header = request.headers.get('Authorization')
#         if not auth_header or not auth_header.startswith('Bearer '):
#             return Response({'error': '토큰 누락 또는 형식 오류'}, status=status.HTTP_401_UNAUTHORIZED)
#
#         token = auth_header.split(' ')[1]
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
#         business_idx = payload.get('company_id')
#         if not business_idx:
#             return Response({'error': '토큰에서 업체 정보 없음'}, status=status.HTTP_401_UNAUTHORIZED)
#
#         # 2. Body에서 정보 추출
#         type_idx = request.data.get('type_idx')
#         name = request.data.get('name')
#         number = request.data.get('number')
#         date_str = request.data.get('date')  # 여기선 문자열 그대로 받음
#
#         if not all([type_idx, name, number, date_str]):
#             return Response({'error': '필수 정보 누락'}, status=status.HTTP_400_BAD_REQUEST)
#
#         # 3. DB insert (날짜 형식 검증 제거)
#         with connection.cursor() as cursor:
#             cursor.execute("""
#                 INSERT INTO data.list (business_idx, type_idx, date, name, number)
#                 VALUES (%s, %s, %s, %s, %s)
#             """, [business_idx, type_idx, date_str, name, number])
#
#         return Response({'message': '등록 성공'}, status=status.HTTP_200_OK)
#
#     except jwt.ExpiredSignatureError:
#         return Response({'error': '토큰 만료'}, status=status.HTTP_401_UNAUTHORIZED)
#     except jwt.InvalidTokenError:
#         return Response({'error': '유효하지 않은 토큰'}, status=status.HTTP_401_UNAUTHORIZED)
#     except Exception as e:
#         return Response({'error': '서버 내부 오류', 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])  # 업로드된 CSV 파일(생산량, 판매량)을 기반으로 분석을 실행합니다.
def analyze_model_outputs(request):
    try:
        file1 = request.FILES.get('file1')
        file2 = request.FILES.get('file2')
        code = request.data.get('code')

        if not all([file1, file2, code]):
            return Response({'error': 'file1, file2, code는 필수입니다.'}, status=400)

        # pandas로 로드
        df_raw1 = pd.read_csv(file1)
        df_raw2 = pd.read_csv(file2)

        # 전처리
        df1 = preprocess_csv_memory(df_raw1)
        df2 = preprocess_csv_memory(df_raw2)

        # 모델 실행 (직접 구현 필요)
        df_result1, df_result2, img1, img2, img3, img4 = run_model_and_get_outputs(df1, df2, code)

        # CSV를 문자열로 변환
        csv1_io = io.StringIO()
        csv2_io = io.StringIO()
        df_result1.to_csv(csv1_io, index=False)
        df_result2.to_csv(csv2_io, index=False)

        # 이미지 base64 인코딩
        images_b64 = []
        for fig in [img1, img2, img3, img4]:
            img_io = io.BytesIO()
            fig.savefig(img_io, format='png')
            img_io.seek(0)
            img_b64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
            images_b64.append(img_b64)

        # JSON 응답
        return Response({
            'csv1': csv1_io.getvalue(),
            'csv2': csv2_io.getvalue(),
            'image1': images_b64[0],
            'image2': images_b64[1],
            'image3': images_b64[2],
            'image4': images_b64[3],
        })

    except Exception as e:
        return Response({'error': '서버 오류', 'detail': str(e)}, status=500)


@api_view(['GET'])
def read_business_data(request):
    try:
        # 1. JWT 토큰 추출
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'error': '토큰 누락 또는 형식 오류'}, status=401)

        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        business_idx = payload.get('company_id')
        if not business_idx:
            return Response({'error': '토큰에 업체 정보 없음'}, status=401)

        # 2. 데이터베이스 조회
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT idx, business_idx, type_idx, date, name, number
                FROM data.list
                WHERE business_idx = %s
                ORDER BY date DESC
            """, [business_idx])
            rows = cursor.fetchall()

        # 3. 결과 가공 - type_idx로 분리
        type1_data = []
        type2_data = []
        for row in rows:
            record = {
                'idx': row[0],
                'business_idx': row[1],
                'type_idx': row[2],
                'date': row[3].strftime('%Y-%m-%d'),
                'name': row[4],
                'number': row[5],
            }
            if row[2] == 1:
                type1_data.append(record)
            elif row[2] == 2:
                type2_data.append(record)

        return Response({
            'type1_data': type1_data,
            'type2_data': type2_data
        }, status=200)

    except jwt.ExpiredSignatureError:
        return Response({'error': '토큰 만료'}, status=401)
    except jwt.InvalidTokenError:
        return Response({'error': '유효하지 않은 토큰'}, status=401)
    except Exception as e:
        return Response({'error': '서버 오류', 'detail': str(e)}, status=500)


