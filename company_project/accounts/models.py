#from django.db import models

# Create your models here.

# from django.db import models
# import random
#
# def generate_unique_code():
#     while True:
#         code = f"{random.randint(0, 999999):06d}"
#         if not Company.objects.filter(code=code).exists():
#             return code
#
# class Company(models.Model):
#     name = models.CharField(max_length=100)  # 상호명
#     ceo_name = models.CharField(max_length=100)
#     email = models.EmailField()
#     phone = models.CharField(max_length=13)
#     code = models.CharField(max_length=6, unique=True, default=generate_unique_code)
#
#     def __str__(self):
#         return f"{self.name} ({self.code})"
