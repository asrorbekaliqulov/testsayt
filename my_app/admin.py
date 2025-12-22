from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Course, Group, TestBlock, Question, TestResult, UserAnswer


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'group', 'is_active']
    list_filter = ['is_active', 'group', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {'fields': ('group',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Qo\'shimcha ma\'lumotlar', {'fields': ('first_name', 'last_name', 'group')}),
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'created_at']
    list_filter = ['course']
    search_fields = ['name']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'order']


@admin.register(TestBlock)
class TestBlockAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'start_time', 'time_per_question', 'is_active']
    list_filter = ['course', 'is_active', 'start_time']
    search_fields = ['title']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['test_block', 'question_text', 'correct_answer', 'order']
    list_filter = ['test_block']
    search_fields = ['question_text']


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'test_block', 'correct_answers', 'total_questions', 'score', 'completed_at']
    list_filter = ['test_block', 'completed_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['user', 'test_block', 'score', 'total_questions', 'correct_answers', 'completed_at', 'time_spent']


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'selected_answer', 'is_correct', 'answered_at']
    list_filter = ['is_correct', 'answered_at']
    search_fields = ['user__username', 'question__question_text']
