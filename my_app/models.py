from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Kurs(models.Model):
    nomi = models.CharField(max_length=100)
    raqami = models.IntegerField(unique=True)
    
    class Meta:
        verbose_name = "Kurs"
        verbose_name_plural = "Kurslar"
    
    def __str__(self):
        return f"{self.raqami}-kurs"

class TestBlock(models.Model):
    BLOCK_TURI = [
        ('ochiq', 'Ochiq test'),
        ('yopiq', 'Yopiq test'),
    ]
    
    VAQT_TURI = [
        ('vaqtli', 'Vaqtli'),
        ('vaqtsiz', 'Vaqtsiz'),
    ]
    
    nomi = models.CharField(max_length=200)
    kurs = models.ForeignKey(Kurs, on_delete=models.CASCADE, related_name='test_blocklari')
    yaratilgan_vaqt = models.DateTimeField(auto_now_add=True)
    
    block_turi = models.CharField(max_length=10, choices=BLOCK_TURI, default='ochiq')
    vaqt_turi = models.CharField(max_length=10, choices=VAQT_TURI, default='vaqtsiz')
    
    # Vaqt sozlamalari
    boshlash_vaqti = models.DateTimeField(null=True, blank=True, help_text="Test boshlash vaqti")
    tugash_vaqti = models.DateTimeField(null=True, blank=True, help_text="Test tugash vaqti")
    savol_vaqti = models.IntegerField(default=60, help_text="Har bir savol uchun vaqt (soniyada)")
    
    # Tanlangan userlar (faqat yopiq testlar uchun)
    tanlangan_userlar = models.ManyToManyField(User, related_name='ruxsat_berilgan_testlar', blank=True)
    
    class Meta:
        verbose_name = "Test Block"
        verbose_name_plural = "Test Blocklar"
    
    def __str__(self):
        return f"{self.nomi} ({self.kurs}) - {self.get_block_turi_display()}"
    
    def is_active(self):
        """Test hozir aktiv ekanligini tekshiradi"""
        if not self.boshlash_vaqti or not self.tugash_vaqti:
            return True  # Vaqt belgilanmagan bo'lsa doim aktiv
        
        hozir = timezone.now()
        return self.boshlash_vaqti <= hozir <= self.tugash_vaqti
    
    def user_can_access(self, user):
        """User testga kira oladimi tekshiradi"""
        if self.block_turi == 'ochiq':
            return True
        else:  # yopiq
            return self.tanlangan_userlar.filter(id=user.id).exists()

class Savol(models.Model):
    block = models.ForeignKey(TestBlock, on_delete=models.CASCADE, related_name='savollar')
    matn = models.TextField()
    rasm = models.ImageField(upload_to='savol_rasmlari/', null=True, blank=True, help_text="Savolga rasm qo'shish (majburiy emas)")
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
    block = models.ForeignKey(TestBlock, on_delete=models.CASCADE, related_name='natijalar')
    togri_javoblar = models.IntegerField(default=0)
    xato_javoblar = models.IntegerField(default=0)
    jami_savollar = models.IntegerField(default=0)
    vaqt_sekund = models.IntegerField()
    topshirilgan_vaqt = models.DateTimeField(auto_now_add=True)
    
    javoblar = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Test Natijasi"
        verbose_name_plural = "Test Natijalari"
        ordering = ['-topshirilgan_vaqt']
    
    def __str__(self):
        return f"{self.user.username} - {self.block.nomi}"
    
    def foiz(self):
        if self.jami_savollar > 0:
            return round((self.togri_javoblar / self.jami_savollar) * 100, 2)
        return 0

class RetestRequest(models.Model):
    STATUS_CHOICES = [
        ('kutilmoqda', 'Kutilmoqda'),
        ('tasdiqlandi', 'Tasdiqlandi'),
        ('rad_etildi', 'Rad etildi'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='retest_requests')
    block = models.ForeignKey(TestBlock, on_delete=models.CASCADE, related_name='retest_requests')
    sabab = models.TextField(help_text="Qayta test ishlash uchun sabab")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='kutilmoqda')
    yuborilgan_vaqt = models.DateTimeField(auto_now_add=True)
    admin_javobi = models.TextField(blank=True, null=True)
    korilgan_vaqt = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Qayta Test So'rovi"
        verbose_name_plural = "Qayta Test So'rovlari"
        ordering = ['-yuborilgan_vaqt']
    
    def __str__(self):
        return f"{self.user.username} - {self.block.nomi} ({self.get_status_display()})"
