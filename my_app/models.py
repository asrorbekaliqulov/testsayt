from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class CustomUser(AbstractUser):
    """Foydalanuvchi modeli"""
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    first_name = models.CharField(max_length=100, verbose_name="Ism")
    last_name = models.CharField(max_length=100, verbose_name="Familiya")
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="Guruh")
    
    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Course(models.Model):
    """Kurs modeli"""
    name = models.CharField(max_length=200, verbose_name="Kurs nomi")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    
    class Meta:
        verbose_name = "Kurs"
        verbose_name_plural = "Kurslar"
    
    def __str__(self):
        return self.name


class Group(models.Model):
    """Guruh modeli"""
    name = models.CharField(max_length=100, verbose_name="Guruh nomi")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups', verbose_name="Kurs")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    
    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"
    
    def __str__(self):
        return f"{self.name} ({self.course.name})"


class TestBlock(models.Model):
    """Test bloki modeli"""
    title = models.CharField(max_length=200, verbose_name="Test nomi")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='test_blocks', verbose_name="Kurs")
    start_time = models.DateTimeField(verbose_name="Boshlanish vaqti")
    time_per_question = models.IntegerField(default=2, verbose_name="Har bir savol uchun vaqt (daqiqa)")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan sana")
    
    class Meta:
        verbose_name = "Test bloki"
        verbose_name_plural = "Test bloklari"
        ordering = ['start_time']
    
    def __str__(self):
        return self.title
    
    def is_unlocked(self):
        """Test ochilganmi tekshirish"""
        return timezone.now() >= self.start_time
    
    def get_end_time(self):
        """Test tugash vaqtini hisoblash"""
        question_count = self.questions.count()
        total_minutes = question_count * self.time_per_question
        from datetime import timedelta
        return self.start_time + timedelta(minutes=total_minutes)
    
    def is_expired(self):
        """Test muddati o'tganmi"""
        return timezone.now() > self.get_end_time()
    
    def can_take_test(self):
        """Test topshirish mumkinmi"""
        return self.is_unlocked() and not self.is_expired() and self.is_active


class Question(models.Model):
    """Savol modeli"""
    test_block = models.ForeignKey(TestBlock, on_delete=models.CASCADE, related_name='questions', verbose_name="Test bloki")
    question_text = models.TextField(verbose_name="Savol matni")
    option_a = models.CharField(max_length=500, verbose_name="A variant")
    option_b = models.CharField(max_length=500, verbose_name="B variant")
    option_c = models.CharField(max_length=500, verbose_name="C variant")
    option_d = models.CharField(max_length=500, verbose_name="D variant")
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], verbose_name="To'g'ri javob")
    order = models.IntegerField(default=0, verbose_name="Tartib raqami")
    
    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.test_block.title} - Savol {self.order}"


class TestResult(models.Model):
    """Test natijasi modeli"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='test_results', verbose_name="Foydalanuvchi")
    test_block = models.ForeignKey(TestBlock, on_delete=models.CASCADE, related_name='results', verbose_name="Test bloki")
    score = models.IntegerField(default=0, verbose_name="Ball")
    total_questions = models.IntegerField(default=0, verbose_name="Jami savollar")
    correct_answers = models.IntegerField(default=0, verbose_name="To'g'ri javoblar")
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name="Topshirilgan vaqt")
    time_spent = models.IntegerField(default=0, verbose_name="Sarflangan vaqt (soniya)")
    
    class Meta:
        verbose_name = "Test natijasi"
        verbose_name_plural = "Test natijalari"
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.test_block.title} ({self.score}%)"
    
    def get_percentage(self):
        if self.total_questions > 0:
            return round((self.correct_answers / self.total_questions) * 100, 2)
        return 0


class UserAnswer(models.Model):
    """Foydalanuvchi javobi modeli"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='answers', verbose_name="Foydalanuvchi")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_answers', verbose_name="Savol")
    selected_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], verbose_name="Tanlangan javob")
    is_correct = models.BooleanField(default=False, verbose_name="To'g'ri javob")
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="Javob berilgan vaqt")
    
    class Meta:
        verbose_name = "Foydalanuvchi javobi"
        verbose_name_plural = "Foydalanuvchi javoblari"
        unique_together = ['user', 'question']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.question.question_text[:50]}"
