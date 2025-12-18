from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Kurs, TestBlock, Savol, TestNatija

@admin.register(Kurs)
class KursAdmin(admin.ModelAdmin):
    list_display = ['nomi', 'raqami']
    list_filter = ['raqami']

class SavolInline(admin.TabularInline):
    model = Savol
    extra = 1
    fields = ['matn', 'variant_a', 'variant_b', 'variant_c', 'variant_d', 'togri_javob']

@admin.register(TestBlock)
class TestBlockAdmin(admin.ModelAdmin):
    list_display = ['nomi', 'kurs', 'yaratilgan_vaqt']
    list_filter = ['kurs', 'yaratilgan_vaqt']
    search_fields = ['nomi']
    inlines = [SavolInline]

@admin.register(Savol)
class SavolAdmin(admin.ModelAdmin):
    list_display = ['matn_qisqa', 'block', 'togri_javob']
    list_filter = ['block', 'togri_javob']
    search_fields = ['matn']
    
    def matn_qisqa(self, obj):
        return obj.matn[:50] + '...' if len(obj.matn) > 50 else obj.matn
    matn_qisqa.short_description = 'Savol matni'

@admin.register(TestNatija)
class TestNatijaAdmin(admin.ModelAdmin):
    list_display = ['user', 'block', 'togri_javoblar', 'xato_javoblar', 'vaqt', 'topshirilgan_vaqt']
    list_filter = ['block', 'topshirilgan_vaqt']
    search_fields = ['user__username', 'block__nomi']
    readonly_fields = ['user', 'block', 'togri_javoblar', 'xato_javoblar', 'vaqt_sekund', 'topshirilgan_vaqt']
    
    def vaqt(self, obj):
        minutes = obj.vaqt_sekund // 60
        seconds = obj.vaqt_sekund % 60
        return f"{minutes}:{seconds:02d}"
    vaqt.short_description = 'Vaqt'