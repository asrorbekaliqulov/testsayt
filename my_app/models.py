from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User

class Kurs(models.Model):
    nomi = models.CharField(max_length=100)
    raqami = models.IntegerField(unique=True)
    
    class Meta:
        verbose_name = "Kurs"
        verbose_name_plural = "Kurslar"
    
    def __str__(self):
        return f"{self.raqami}-kurs"

class TestBlock(models.Model):
    nomi = models.CharField(max_length=200)
    kurs = models.ForeignKey(Kurs, on_delete=models.CASCADE, related_name='test_blocklari')
    yaratilgan_vaqt = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Test Block"
        verbose_name_plural = "Test Blocklar"
    
    def __str__(self):
        return f"{self.nomi} ({self.kurs})"

class Savol(models.Model):
    block = models.ForeignKey(TestBlock, on_delete=models.CASCADE, related_name='savollar')
    matn = models.TextField()
    variant_a = models.CharField(max_length=500)
    variant_b = models.CharField(max_length=500)
    variant_c = models.CharField(max_length=500)
    variant_d = models.CharField(max_length=500)
    togri_javob = models.CharField(max_length=1, choices=[
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ])
    
    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"
    
    def __str__(self):
        return self.matn[:50]

class TestNatija(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    block = models.ForeignKey(TestBlock, on_delete=models.CASCADE)
    togri_javoblar = models.IntegerField(default=0)
    xato_javoblar = models.IntegerField(default=0)
    vaqt_sekund = models.IntegerField()
    topshirilgan_vaqt = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Test Natijasi"
        verbose_name_plural = "Test Natijalari"
    
    def __str__(self):
        return f"{self.user.username} - {self.block.nomi}"
