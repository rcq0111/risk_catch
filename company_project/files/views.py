import base64

import numpy as np
from django.db import connection
from datetime import datetime
import pandas as pd
import io
import jwt
from django.conf import settings
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, FileResponse
from .your_model_module import run_model_and_get_outputs


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

        # 2. Body에서 정보 추출
        type_idx = request.data.get('type_idx')
        name = request.data.get('name')
        number = request.data.get('number')
        date_str = request.data.get('date')

        if not all([type_idx, name, number, date_str]):
            return Response({'error': '필수 정보 누락'}, status=status.HTTP_400_BAD_REQUEST)

        # 날짜 형식 검증 및 변환
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({'error': '날짜 형식 오류 (예: 2023-01-02)'}, status=status.HTTP_400_BAD_REQUEST)

        # 3. DB insert
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO data.list (business_idx, type_idx, date, name, number)
                VALUES (%s, %s, %s, %s, %s)
            """, [business_idx, type_idx, date, name, number])

        return Response({'message': '등록 성공'}, status=status.HTTP_200_OK)

    except jwt.ExpiredSignatureError:
        return Response({'error': '토큰 만료'}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({'error': '유효하지 않은 토큰'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'error': '서버 내부 오류', 'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def analyze_model_outputs(request):
    try:
        file1 = request.FILES.get('file1')
        file2 = request.FILES.get('file2')
        code = request.data.get('code')

        if not all([file1, file2, code]):
            return Response({'error': 'file1, file2, code는 필수입니다.'}, status=400)

        # pandas로 읽기
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)

        # 모델 실행 (직접 구현 필요)
        df_result1, df_result2, img1, img2, img3, img4 = run_model_and_get_outputs(df1, df2, code)

        # CSV 응답 준비
        csv1_io = io.StringIO()
        csv2_io = io.StringIO()
        df_result1.to_csv(csv1_io, index=False)
        df_result2.to_csv(csv2_io, index=False)

        # 이미지 바이너리 응답 준비
        img_io_list = []
        for fig in [img1, img2, img3, img4]:
            img_io = io.BytesIO()
            fig.savefig(img_io, format='png')
            img_io.seek(0)
            img_io_list.append(img_io)

        # Multipart 응답
        response = HttpResponse(content_type='multipart/mixed; boundary=boundary123')
        response.write('--boundary123\r\n')
        response.write('Content-Type: text/csv\r\nContent-Disposition: attachment; filename="result1.csv"\r\n\r\n')
        response.write(csv1_io.getvalue())
        response.write('\r\n--boundary123\r\n')
        response.write('Content-Type: text/csv\r\nContent-Disposition: attachment; filename="result2.csv"\r\n\r\n')
        response.write(csv2_io.getvalue())

        for i, img_io in enumerate(img_io_list, 1):
            response.write(f'\r\n--boundary123\r\n')
            response.write(f'Content-Type: image/png\r\nContent-Disposition: attachment; filename="chart{i}.png"\r\n\r\n')
            response.write(img_io.getvalue())

        response.write('\r\n--boundary123--')
        return response

    except Exception as e:
        return Response({'error': '서버 오류', 'detail': str(e)}, status=500)

# import pandas as pd
# import io
# import matplotlib.pyplot as plt
# from rest_framework.decorators import api_view
#
#
# @api_view(['POST'])
# @parser_classes([MultiPartParser, FormParser])
# def analyze_model_input(request):
#     try:
#         file1 = request.FILES.get('file1')
#         file2 = request.FILES.get('file2')
#         code = request.data.get('code')
#
#         if not file1 or not file2 or not code:
#             return Response({'error': '필수 입력 누락'}, status=400)
#
#         # 실제 모델이 들어갈 자리 (지금은 더미 데이터)
#         df1 = pd.read_csv(file1)
#         df2 = pd.read_csv(file2)
#
#         # 더미 결과 CSV
#         result_csv_1 = io.StringIO()
#         result_csv_2 = io.StringIO()
#         pd.DataFrame({'제품': ['A', 'B'], '수량': [10, 20]}).to_csv(result_csv_1, index=False)
#         pd.DataFrame({'지역': ['서울', '부산'], '판매량': [100, 80]}).to_csv(result_csv_2, index=False)
#         result_csv_1.seek(0)
#         result_csv_2.seek(0)
#
#         # 더미 이미지 생성
#         image_buffers = []
#         for i in range(4):
#             fig, ax = plt.subplots()
#             ax.plot(np.random.rand(10))
#             buf = io.BytesIO()
#             fig.savefig(buf, format='png')
#             buf.seek(0)
#             image_buffers.append(buf)
#             plt.close(fig)
#
#         return Response({
#             'csv1': result_csv_1.getvalue(),
#             'csv2': result_csv_2.getvalue(),
#             'image1': base64.b64encode(image_buffers[0].read()).decode(),
#             'image2': base64.b64encode(image_buffers[1].read()).decode(),
#             'image3': base64.b64encode(image_buffers[2].read()).decode(),
#             'image4': base64.b64encode(image_buffers[3].read()).decode(),
#         }, status=200)
#
#     except Exception as e:
#         return Response({'error': '서버 오류', 'detail': str(e)}, status=500)

import jwt
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import connection

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

        # 3. 결과 가공
        results = []
        for row in rows:
            results.append({
                'idx': row[0],
                'business_idx': row[1],
                'type_idx': row[2],
                'date': row[3].strftime('%Y-%m-%d'),
                'name': row[4],
                'number': row[5],
            })

        return Response({'data': results}, status=200)

    except jwt.ExpiredSignatureError:
        return Response({'error': '토큰 만료'}, status=401)
    except jwt.InvalidTokenError:
        return Response({'error': '유효하지 않은 토큰'}, status=401)
    except Exception as e:
        return Response({'error': '서버 오류', 'detail': str(e)}, status=500)
