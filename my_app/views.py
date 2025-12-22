from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q, Avg, Count, Max
from .models import CustomUser, Course, Group, TestBlock, Question, TestResult, UserAnswer
import json


def login_view(request):
    """Login sahifasi"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Username yoki parol noto\'g\'ri!')
    
    return render(request, 'login.html')


def logout_view(request):
    """Logout"""
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    """Asosiy sahifa - test bloklari"""
    user = request.user
    
    # Foydalanuvchi guruhiga tegishli kursni topish
    if user.group:  # Bu yerda user.groups.exists() kerak emas
        test_blocks = TestBlock.objects.filter(course=user.group.course, is_active=True)
    else:
        test_blocks = TestBlock.objects.filter(is_active=True)
    
    # Har bir blok uchun holatni aniqlash
    blocks_data = []
    for block in test_blocks:
        # Foydalanuvchi bu testni topshirganmi?
        # user allaqachon CustomUser instance, qayta get qilish kerak emas!
        completed = TestResult.objects.filter(user=user, test_block=block).exists()
        
        blocks_data.append({
            'block': block,
            'is_locked': not block.is_unlocked(),
            'is_expired': block.is_expired(),
            'can_take': block.can_take_test() and not completed,
            'completed': completed,
        })
    
    context = {
        'user': user,
        'blocks_data': blocks_data,
    }
    return render(request, 'dashboard.html', context)
@login_required
def take_test(request, test_id):
    """Test topshirish sahifasi"""
    test_block = get_object_or_404(TestBlock, id=test_id)
    user = request.user
    
    # Test topshirish mumkinmi tekshirish
    if not test_block.can_take_test():
        messages.error(request, 'Bu test hozir mavjud emas!')
        return redirect('dashboard')
    
    # Allaqachon topshirganmi?
    if TestResult.objects.filter(user=user, test_block=test_block).exists():
        messages.error(request, 'Siz bu testni allaqachon topshirgansiz!')
        return redirect('dashboard')
    
    questions = test_block.questions.all()
    
    context = {
        'test_block': test_block,
        'questions': questions,
        'total_time': test_block.questions.count() * test_block.time_per_question * 60,  # soniyada
        'end_time': test_block.get_end_time().isoformat(),
    }
    return render(request, 'take_test.html', context)


@login_required
def submit_test(request, test_id):
    """Test natijasini saqlash"""
    if request.method != 'POST':
        return redirect('dashboard')
    
    test_block = get_object_or_404(TestBlock, id=test_id)
    user = request.user
    
    # Allaqachon topshirganmi?
    if TestResult.objects.filter(user=user, test_block=test_block).exists():
        messages.error(request, 'Siz bu testni allaqachon topshirgansiz!')
        return redirect('dashboard')
    
    # Test vaqti tugaganmi?
    if test_block.is_expired():
        messages.error(request, 'Test vaqti tugagan!')
        return redirect('dashboard')
    
    # Javoblarni olish
    data = json.loads(request.body)
    answers = data.get('answers', {})
    time_spent = data.get('time_spent', 0)
    
    questions = test_block.questions.all()
    correct_count = 0
    
    # Har bir javobni tekshirish va saqlash
    for question in questions:
        selected = answers.get(str(question.id))
        if selected:
            is_correct = selected == question.correct_answer
            if is_correct:
                correct_count += 1
            
            UserAnswer.objects.create(
                user=user,
                question=question,
                selected_answer=selected,
                is_correct=is_correct
            )
    
    # Natijani hisoblash
    total_questions = questions.count()
    score = round((correct_count / total_questions) * 100, 2) if total_questions > 0 else 0
    
    # Natijani saqlash
    result = TestResult.objects.create(
        user=user,
        test_block=test_block,
        score=score,
        total_questions=total_questions,
        correct_answers=correct_count,
        time_spent=time_spent
    )
    
    return JsonResponse({
        'success': True,
        'result_id': result.id,
        'score': score,
        'correct': correct_count,
        'total': total_questions
    })


@login_required
def view_result(request, result_id):
    """Natijani ko'rish"""
    result = get_object_or_404(TestResult, id=result_id, user=request.user)
    
    # Foydalanuvchi javoblarini olish
    user_answers = UserAnswer.objects.filter(
        user=request.user,
        question__test_block=result.test_block
    ).select_related('question')
    
    context = {
        'result': result,
        'user_answers': user_answers,
    }
    return render(request, 'result.html', context)


# Custom Admin Panel Views
def is_admin(user):
    """Admin ekanligini tekshirish"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Custom admin bosh sahifa"""
    total_users = CustomUser.objects.filter(is_staff=False).count()
    total_courses = Course.objects.count()
    total_tests = TestBlock.objects.count()
    total_results = TestResult.objects.count()
    
    # Oxirgi natijalar
    recent_results = TestResult.objects.select_related('user', 'test_block').order_by('-completed_at')[:10]
    
    context = {
        'total_users': total_users,
        'total_courses': total_courses,
        'total_tests': total_tests,
        'total_results': total_results,
        'recent_results': recent_results,
    }
    return render(request, 'admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_users(request):
    """Foydalanuvchilar ro'yxati"""
    users = CustomUser.objects.filter(is_staff=False).select_related('group', 'group__course')
    
    context = {
        'users': users,
    }
    return render(request, 'admin/users.html', context)


@login_required
@user_passes_test(is_admin)
def admin_add_user(request):
    """Yangi foydalanuvchi qo'shish"""
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        group_id = request.POST.get('group')
        
        # Username mavjudmi tekshirish
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Bu username allaqachon mavjud!')
        else:
            group = Group.objects.get(id=group_id) if group_id else None
            user = CustomUser.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                group=group
            )
            messages.success(request, 'Foydalanuvchi muvaffaqiyatli qo\'shildi!')
            return redirect('admin_users')
    
    groups = Group.objects.select_related('course').all()
    context = {
        'groups': groups,
    }
    return render(request, 'admin/add_user.html', context)


@login_required
@user_passes_test(is_admin)
def admin_edit_user(request, user_id):
    """Foydalanuvchini tahrirlash"""
    user = get_object_or_404(CustomUser, id=user_id, is_staff=False)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        group_id = request.POST.get('group')
        password = request.POST.get('password')
        
        if group_id:
            user.group = Group.objects.get(id=group_id)
        
        if password:
            user.set_password(password)
        
        user.save()
        messages.success(request, 'Foydalanuvchi muvaffaqiyatli yangilandi!')
        return redirect('admin_users')
    
    groups = Group.objects.select_related('course').all()
    context = {
        'edit_user': user,
        'groups': groups,
    }
    return render(request, 'admin/edit_user.html', context)


@login_required
@user_passes_test(is_admin)
def admin_results(request):
    """Barcha natijalar"""
    results = TestResult.objects.select_related('user', 'test_block').order_by('-completed_at')
    
    # Filter by test block
    test_id = request.GET.get('test')
    if test_id:
        results = results.filter(test_block_id=test_id)
    
    # Filter by course
    course_id = request.GET.get('course')
    if course_id:
        results = results.filter(test_block__course_id=course_id)
    
    test_blocks = TestBlock.objects.all()
    courses = Course.objects.all()
    
    context = {
        'results': results,
        'test_blocks': test_blocks,
        'courses': courses,
    }
    return render(request, 'admin/results.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_results(request, user_id):
    """Bitta foydalanuvchining barcha natijalari"""
    user = get_object_or_404(CustomUser, id=user_id)
    results = TestResult.objects.filter(user=user).select_related('test_block').order_by('-completed_at')
    
    context = {
        'view_user': user,
        'results': results,
    }
    return render(request, 'admin/user_results.html', context)


@login_required
@user_passes_test(is_admin)
def admin_courses(request):
    """Kurslar ro'yxati"""
    courses = Course.objects.annotate(
        group_count=Count('groups'),
        student_count=Count('groups__students')
    ).order_by('-created_at')
    
    context = {
        'courses': courses,
    }
    return render(request, 'admin/courses.html', context)


@login_required
@user_passes_test(is_admin)
def admin_add_course(request):
    """Yangi kurs qo'shish"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            Course.objects.create(
                name=name,
                description=description
            )
            messages.success(request, 'Kurs muvaffaqiyatli qo\'shildi!')
            return redirect('admin_courses')
        else:
            messages.error(request, 'Kurs nomi kiritilishi shart!')
    
    return render(request, 'admin/course_form.html')


@login_required
@user_passes_test(is_admin)
def admin_edit_course(request, course_id):
    """Kursni tahrirlash"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course.name = request.POST.get('name')
        course.description = request.POST.get('description', '')
        course.save()
        messages.success(request, 'Kurs muvaffaqiyatli yangilandi!')
        return redirect('admin_courses')
    
    context = {
        'course': course,
    }
    return render(request, 'admin/course_form.html', context)


@login_required
@user_passes_test(is_admin)
def admin_delete_course(request, course_id):
    """Kursni o'chirish"""
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        course.delete()
        messages.success(request, 'Kurs muvaffaqiyatli o\'chirildi!')
    return redirect('admin_courses')


@login_required
@user_passes_test(is_admin)
def admin_groups(request):
    """Guruhlar ro'yxati"""
    groups = Group.objects.select_related('course').annotate(
        student_count=Count('students')
    ).order_by('-created_at')
    
    context = {
        'groups': groups,
    }
    return render(request, 'admin/groups.html', context)


@login_required
@user_passes_test(is_admin)
def admin_add_group(request):
    """Yangi guruh qo'shish"""
    if request.method == 'POST':
        name = request.POST.get('name')
        course_id = request.POST.get('course')
        description = request.POST.get('description', '')
        
        if name and course_id:
            course = get_object_or_404(Course, id=course_id)
            Group.objects.create(
                name=name,
                course=course,
                description=description
            )
            messages.success(request, 'Guruh muvaffaqiyatli qo\'shildi!')
            return redirect('admin_groups')
        else:
            messages.error(request, 'Guruh nomi va kurs tanlanishi shart!')
    
    courses = Course.objects.all()
    context = {
        'courses': courses,
    }
    return render(request, 'admin/group_form.html', context)


@login_required
@user_passes_test(is_admin)
def admin_edit_group(request, group_id):
    """Guruhni tahrirlash"""
    group = get_object_or_404(Group, id=group_id)
    
    if request.method == 'POST':
        group.name = request.POST.get('name')
        course_id = request.POST.get('course')
        group.description = request.POST.get('description', '')
        
        if course_id:
            group.course = get_object_or_404(Course, id=course_id)
        
        group.save()
        messages.success(request, 'Guruh muvaffaqiyatli yangilandi!')
        return redirect('admin_groups')
    
    courses = Course.objects.all()
    context = {
        'group': group,
        'courses': courses,
    }
    return render(request, 'admin/group_form.html', context)


@login_required
@user_passes_test(is_admin)
def admin_delete_group(request, group_id):
    """Guruhni o'chirish"""
    if request.method == 'POST':
        group = get_object_or_404(Group, id=group_id)
        group.delete()
        messages.success(request, 'Guruh muvaffaqiyatli o\'chirildi!')
    return redirect('admin_groups')


@login_required
@user_passes_test(is_admin)
def admin_test_blocks(request):
    """Test bloklari ro'yxati"""
    test_blocks = TestBlock.objects.select_related('course').annotate(
        question_count=Count('questions'),
        result_count=Count('results')
    ).order_by('-created_at')
    
    context = {
        'test_blocks': test_blocks,
    }
    return render(request, 'admin/test_blocks.html', context)


@login_required
@user_passes_test(is_admin)
def admin_add_test_block(request):
    """Yangi test bloki qo'shish"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        course_id = request.POST.get('course')
        start_time = request.POST.get('start_time')
        time_per_question = request.POST.get('time_per_question')
        
        if title and course_id and start_time and time_per_question:
            course = get_object_or_404(Course, id=course_id)
            TestBlock.objects.create(
                title=title,
                description=description,
                course=course,
                start_time=start_time,
                time_per_question=int(time_per_question)
            )
            messages.success(request, 'Test bloki muvaffaqiyatli qo\'shildi!')
            return redirect('admin_test_blocks')
        else:
            messages.error(request, 'Barcha maydonlarni to\'ldiring!')
    
    courses = Course.objects.all()
    context = {
        'courses': courses,
    }
    return render(request, 'admin/test_block_form.html', context)


@login_required
@user_passes_test(is_admin)
def admin_edit_test_block(request, block_id):
    """Test blokini tahrirlash"""
    test_block = get_object_or_404(TestBlock, id=block_id)
    
    if request.method == 'POST':
        test_block.title = request.POST.get('title')
        test_block.description = request.POST.get('description', '')
        course_id = request.POST.get('course')
        test_block.start_time = request.POST.get('start_time')
        test_block.time_per_question = int(request.POST.get('time_per_question'))
        test_block.is_active = request.POST.get('is_active') == 'on'
        
        if course_id:
            test_block.course = get_object_or_404(Course, id=course_id)
        
        test_block.save()
        messages.success(request, 'Test bloki muvaffaqiyatli yangilandi!')
        return redirect('admin_test_blocks')
    
    courses = Course.objects.all()
    # Format datetime for input field
    start_time_formatted = test_block.start_time.strftime('%Y-%m-%dT%H:%M')
    
    context = {
        'test_block': test_block,
        'courses': courses,
        'start_time_formatted': start_time_formatted,
    }
    return render(request, 'admin/test_block_form.html', context)


@login_required
@user_passes_test(is_admin)
def admin_delete_test_block(request, block_id):
    """Test blokini o'chirish"""
    if request.method == 'POST':
        test_block = get_object_or_404(TestBlock, id=block_id)
        test_block.delete()
        messages.success(request, 'Test bloki muvaffaqiyatli o\'chirildi!')
    return redirect('admin_test_blocks')


@login_required
@user_passes_test(is_admin)
def admin_test_questions(request, block_id):
    """Test blokidagi savollar ro'yxati"""
    test_block = get_object_or_404(TestBlock, id=block_id)
    questions = test_block.questions.all().order_by('order')
    
    context = {
        'test_block': test_block,
        'questions': questions,
    }
    return render(request, 'admin/test_questions.html', context)


@login_required
@user_passes_test(is_admin)
def admin_add_question(request, block_id):
    """Yangi savol qo'shish"""
    test_block = get_object_or_404(TestBlock, id=block_id)
    
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        option_a = request.POST.get('option_a')
        option_b = request.POST.get('option_b')
        option_c = request.POST.get('option_c')
        option_d = request.POST.get('option_d')
        correct_answer = request.POST.get('correct_answer')
        order = request.POST.get('order', 0)
        
        if all([question_text, option_a, option_b, option_c, option_d, correct_answer]):
            Question.objects.create(
                test_block=test_block,
                question_text=question_text,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_answer=correct_answer,
                order=int(order)
            )
            messages.success(request, 'Savol muvaffaqiyatli qo\'shildi!')
            return redirect('admin_test_questions', block_id=block_id)
        else:
            messages.error(request, 'Barcha maydonlarni to\'ldiring!')
    
    # Get next order number
    max_order = test_block.questions.aggregate(Max('order'))['order__max'] or 0
    next_order = max_order + 1
    
    context = {
        'test_block': test_block,
        'next_order': next_order,
    }
    return render(request, 'admin/question_form.html', context)


@login_required
@user_passes_test(is_admin)
def admin_edit_question(request, question_id):
    """Savolni tahrirlash"""
    question = get_object_or_404(Question, id=question_id)
    test_block = question.test_block
    
    if request.method == 'POST':
        question.question_text = request.POST.get('question_text')
        question.option_a = request.POST.get('option_a')
        question.option_b = request.POST.get('option_b')
        question.option_c = request.POST.get('option_c')
        question.option_d = request.POST.get('option_d')
        question.correct_answer = request.POST.get('correct_answer')
        question.order = int(request.POST.get('order', 0))
        
        question.save()
        messages.success(request, 'Savol muvaffaqiyatli yangilandi!')
        return redirect('admin_test_questions', block_id=test_block.id)
    
    context = {
        'question': question,
        'test_block': test_block,
    }
    return render(request, 'admin/question_form.html', context)


@login_required
@user_passes_test(is_admin)
def admin_delete_question(request, question_id):
    """Savolni o'chirish"""
    if request.method == 'POST':
        question = get_object_or_404(Question, id=question_id)
        block_id = question.test_block.id
        question.delete()
        messages.success(request, 'Savol muvaffaqiyatli o\'chirildi!')
        return redirect('admin_test_questions', block_id=block_id)
    return redirect('admin_test_blocks')
