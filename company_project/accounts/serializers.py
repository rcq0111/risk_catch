# from rest_framework import serializers
# from .models import Company
# import re
#
# class CompanySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Company
#         fields = ['name', 'ceo_name', 'email', 'phone', 'code']
#         read_only_fields = ['code']
#
#     def validate_name(self, value):
#         if not re.match(r'^[가-힣a-zA-Z0-9]+$', value):
#             raise serializers.ValidationError("상호명은 한글, 영문, 숫자만 포함됩니다.")
#         return value
#
#     def validate_phone(self, value):
#         if not re.match(r'^010-\d{4}-\d{4}$', value):
#             raise serializers.ValidationError("전화번호는 010-0000-0000 형식이어야 합니다.")
#         return value
