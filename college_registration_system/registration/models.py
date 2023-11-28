import random
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.hashers import make_password
from django.db.models.signals import post_save, post_delete
from django.db.models import UniqueConstraint
from django.db.models import F
import uuid
from django.dispatch import receiver


# User Model
class User(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    USER_TYPE_CHOICES = [
        ('Admin', 'Admin'),
        ('Student', 'Student'),
        ('Faculty', 'Faculty'),
    ]
    # id = models.AutoField(primary_key=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)
    dob = models.DateField(default='2000-01-01')
    street = models.CharField(max_length=100,null=True)
    city = models.CharField(max_length=50,null=True)
    state = models.CharField(max_length=50,null=True)
    zip_code = models.CharField(max_length=10,null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)

    def __str__(self):
        return self.first_name + ' ' + self.last_name + ' ' + self.user_type

@receiver(post_save, sender=User)
def create_or_update_user_login(sender, instance, created, **kwargs):
    try:
        login_instance = Login.objects.get(user_id=instance.id)
        if login_instance.is_superuser:
            return  # Skip if it's a superuser
    except Login.DoesNotExist:
        pass  # Continue if Login does not exist

    if created:
        #create email from first and last name
        email = f"{instance.first_name[0].lower()}{instance.last_name.lower()}@mikehawk.edu"
        #if another user has the same email, add a sequence number to the email
        i=1
        while Login.objects.filter(email=email).exists():
            email = f"{instance.first_name[0].lower()}{instance.last_name.lower()}{i}@mikehawk.edu"
            i+=1

        password = make_password("123456")  # Hash the default password
        #if login already exists, do not create login
        try:
            Login.objects.create(
                user_id=instance.id,
                email=email,
                password=password,
                no_of_attempts=0,
                is_locked=False
            )
        except:
            pass
    try:
        if instance.user_type == 'Admin':
            Admin.objects.get_or_create(user_id=instance.id)
            #delete other subtypes
            Student.objects.filter(user_id=instance.id).delete()
            Faculty.objects.filter(user_id=instance.id).delete()
        elif instance.user_type == 'Student':
            Student.objects.get_or_create(user_id=instance.id)
            #delete other subtypes
            Admin.objects.filter(user_id=instance.id).delete()
            Faculty.objects.filter(user_id=instance.id).delete()
        elif instance.user_type == 'Faculty':
            Faculty.objects.get_or_create(user_id=instance.id)
            #delete other subtypes
            Admin.objects.filter(user_id=instance.id).delete()
            Student.objects.filter(user_id=instance.id).delete()
    except:
        pass


# Login Model
class LoginManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        # Step 1: Create a User entity
        user_obj = User.objects.create(
            first_name=extra_fields.get('first_name', ''),
            last_name=extra_fields.get('last_name', ''),
            user_type=extra_fields.get('user_type', 'Student'),  # Default to 'Student'
            # ... other fields ...
        )

        # Step 2: Create the Login entity and link it to the User entity
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        user = self.model(email=email, user_id=user_obj.id, **extra_fields)

        user.password = make_password(password)  # Hash the password
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # Step 1: Create a User entity with UserType set to 'Admin'
        user_obj = User.objects.create(
            first_name = 'Admin',
            last_name = 'Admin',
            user_type='Admin',  # Set UserType to 'Admin'
            # ... other fields ...
        )

        # Step 2: Create the Login entity and link it to the User entity
        user = self.model(email=email, user_id=user_obj.id, **extra_fields)
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.user_type = 'Admin'  # Set UserType to 'Admin'
        user.save(using=self._db)

        # Step 3: Create the Admin entity and link it to the User entity
        Admin.objects.create(
            user_id=user_obj.id,
            access_level=extra_fields.get('access_level', 2)  # Set access level or use a default
        )

        return user

class Login(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    no_of_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    objects = LoginManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def __str__(self):
        return self.email

# Admin Model
class Admin(models.Model):
    ACCESS_LEVEL_CHOICES = [
        (1, 'Level 1'),
        (2, 'Level 2'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    access_level = models.IntegerField(choices=ACCESS_LEVEL_CHOICES, default=2)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

# Student Model
class Student(models.Model):
    #studentID which would auto increment from 700000000
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    studentID = models.IntegerField(unique=True, blank=True, null=True)
    major_id = models.ForeignKey('Major', on_delete=models.SET_NULL, null=True, blank=True)
    minor_id = models.ForeignKey('Minor', on_delete=models.SET_NULL, null=True, blank=True)
    enrollment_year = models.IntegerField(null=True)
    STUDENT_TYPE_CHOICES = [
        ('Undergraduate', 'Undergraduate'),
        ('Graduate', 'Graduate'),
    ]
    student_type = models.CharField(max_length=15, choices=STUDENT_TYPE_CHOICES)

    def save(self, *args, **kwargs):
        if not self.studentID:
            # Get the last studentID and increment it by 1
            last_student = Student.objects.all().order_by('-studentID').first()
            if last_student:
                self.studentID = last_student.studentID + 1
            else:
                self.studentID = 700000  # This is the first student
        super(Student, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.studentID} - {self.user.first_name} {self.user.last_name}"


@receiver(post_save, sender=Student)
def create_student_subtype(sender, instance, created, **kwargs):
    student_type = instance.student_type

    if student_type == 'Undergraduate':
        Undergraduate.objects.get_or_create(student=instance)
        Graduate.objects.filter(student=instance).delete()
    elif student_type == 'Graduate':
        Graduate.objects.get_or_create(student=instance)
        Undergraduate.objects.filter(student=instance).delete()

# Undergraduate Model
class Undergraduate(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, primary_key=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)
    UNDERGRAD_STUDENT_TYPE_CHOICES = [
        ('FullTime', 'Full-Time'),
        ('PartTime', 'Part-Time'),
    ]
    undergrad_student_type = models.CharField(max_length=8, choices=UNDERGRAD_STUDENT_TYPE_CHOICES)

    def __str__(self):
        return self.student.user.first_name + ' ' + self.student.user.last_name


# Undergrad_Full_Time Model
class Undergrad_Full_Time(models.Model):
    student = models.OneToOneField(Undergraduate, on_delete=models.CASCADE, primary_key=True)
    STANDING_CHOICES = [
        ('Fresh', 'Freshman'),
        ('Sophomore', 'Sophomore'),
        ('Junior', 'Junior'),
        ('Senior', 'Senior'),
        # Add other standings as needed
    ]
    standing = models.CharField(max_length=10, choices=STANDING_CHOICES)
    min_creds = models.IntegerField(default=9)
    max_creds = models.IntegerField(default=16)
    creds_earned = models.IntegerField(default=0)

    def __str__(self):
        return self.student.student.user.first_name + ' ' + self.student.student.user.last_name

# Undergrad_Part_Time Model
class Undergrad_Part_Time(models.Model):
    student = models.OneToOneField(Undergraduate, on_delete=models.CASCADE, primary_key=True)
    STANDING_CHOICES = [
        ('Fresh', 'Freshman'),
        ('Sophomore', 'Sophomore'),
        ('Junior', 'Junior'),
        ('Senior', 'Senior'),
        # Add other standings as needed
    ]
    standing = models.CharField(max_length=10, choices=STANDING_CHOICES)
    min_creds = models.IntegerField(default=3)
    max_creds = models.IntegerField(default=8)
    creds_earned = models.IntegerField(default=0)

    def __str__(self):
        return self.student.student.user.first_name + ' ' + self.student.student.user.last_name

@receiver(post_save, sender=Undergraduate)
def create_or_update_undergrad_subtype(sender, instance, **kwargs):
    student_type = instance.undergrad_student_type

    if student_type == 'FullTime':
        Undergrad_Full_Time.objects.get_or_create(student=instance)
        Undergrad_Part_Time.objects.filter(student=instance).delete()
    elif student_type == 'PartTime':
        Undergrad_Part_Time.objects.get_or_create(student=instance)
        Undergrad_Full_Time.objects.filter(student=instance).delete()

# Graduate Model
class Graduate(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, primary_key=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)
    PROGRAM_CHOICES = [
        ('Masters', 'Masters'),
        ('PHD', 'PHD'),
    ]
    program = models.CharField(max_length=7, choices=PROGRAM_CHOICES)
    GRAD_STUDENT_TYPE_CHOICES = [
        ('FullTime', 'Full-Time'),
        ('PartTime', 'Part-Time'),
    ]
    grad_student_type = models.CharField(max_length=8, choices=GRAD_STUDENT_TYPE_CHOICES)

    def __str__(self):
        return self.student.user.first_name + ' ' + self.student.user.last_name

# Grad_Full_Time Model
class Grad_Full_Time(models.Model):
    student = models.OneToOneField(Graduate, on_delete=models.CASCADE, primary_key=True)
    year = models.IntegerField(default = 2023)
    credits_earned = models.IntegerField(default=0)
    qualifying_exam = models.BooleanField(default=False)
    thesis = models.BooleanField(default=False)

    def __str__(self):
        return self.student.student.user.first_name + ' ' + self.student.student.user.last_name
# Grad_Part_Time Model
class Grad_Part_Time(models.Model):
    student = models.OneToOneField(Graduate, on_delete=models.CASCADE, primary_key=True)
    year = models.IntegerField(default = 2023)
    credits_earned = models.IntegerField(default=0)
    qualifying_exam = models.BooleanField(default=False)
    thesis = models.BooleanField(default=False)

    def __str__(self):
        return self.student.student.user.first_name + ' ' + self.student.student.user.last_name

@receiver(post_save, sender=Graduate)
def create_or_update_grad_subtype(sender, instance, **kwargs):
    student_type = instance.grad_student_type

    if student_type == 'FullTime':
        Grad_Full_Time.objects.get_or_create(student=instance)
        Grad_Part_Time.objects.filter(student=instance).delete()
    elif student_type == 'PartTime':
        Grad_Part_Time.objects.get_or_create(student=instance)
        Grad_Full_Time.objects.filter(student=instance).delete()

# Faculty Model
class Faculty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    RANK_CHOICES = [
        ('Professor', 'Professor'),
        ('Assistant Professor', 'Assistant Professor'),
        ('Adjunct Professor', 'Adjunct'),
        ('Teaching Assistant', 'Teaching Assistant'),
        # Add other ranks as needed
    ]
    rank = models.CharField(max_length=24, choices=RANK_CHOICES)
    #can be multiple departments. Should be a foreign key list
    departments = models.ManyToManyField('Department')
    specialty = models.CharField(max_length=50, null=True, blank=True)
    FAC_TYPE_CHOICES = [
        ('FullTime', 'Full-Time'),
        ('PartTime', 'Part-Time'),
    ]
    fac_type = models.CharField(max_length=8, choices=FAC_TYPE_CHOICES)

    def __str__(self):
        return self.rank +' '+self.user.first_name + ' ' + self.user.last_name
# Faculty_FullTime Model
class Faculty_FullTime(models.Model):
    faculty = models.OneToOneField(Faculty, on_delete=models.CASCADE, primary_key=True)
    num_of_courses = models.IntegerField( default=0)
    office = models.ForeignKey('Room', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.faculty.rank +' '+self.faculty.user.first_name + ' ' + self.faculty.user.last_name
# Faculty_PartTime Model
class Faculty_PartTime(models.Model):
    faculty = models.OneToOneField(Faculty, on_delete=models.CASCADE, primary_key=True)
    num_of_courses = models.IntegerField( default=0)
    office = models.ForeignKey('Room', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.faculty.rank +' '+self.faculty.user.first_name + ' ' + self.faculty.user.last_name

#when fac_type is changed, update subtype and delete old subtype
@receiver(post_save, sender=Faculty)
def create_or_update_faculty_subtype(sender, instance, **kwargs):
    fac_type = instance.fac_type

    if fac_type == 'FullTime':
        Faculty_FullTime.objects.get_or_create(faculty=instance)
        Faculty_PartTime.objects.filter(faculty=instance).delete()
    elif fac_type == 'PartTime':
        Faculty_PartTime.objects.get_or_create(faculty=instance)
        Faculty_FullTime.objects.filter(faculty=instance).delete()

# StatisticsOffice Model
class StatisticsOffice(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    ACCESS_LEVEL_CHOICES = [
        (1, 'Level 1'),
        (2, 'Level 2'),
    ]
    access_level = models.IntegerField(choices=ACCESS_LEVEL_CHOICES)

    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

class Major(models.Model):
    major_name = models.CharField(max_length=50)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.major_name

class Minor(models.Model):
    minor_name = models.CharField(max_length=50)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.minor_name

# Dept Model
class Department(models.Model):
    department_id = models.CharField(max_length=10, primary_key=True)
    department_name = models.CharField(max_length=50)
    chair_id = models.ForeignKey('Faculty', related_name='chair', on_delete=models.SET_NULL, null=True, blank=True)
    manager_id = models.ForeignKey('Faculty', related_name='manager', on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    room_id = models.ForeignKey('Room', on_delete=models.SET_NULL, null=True,blank=True)

    def __str__(self):
        return self.department_name
# Building Model
class Building(models.Model):
    BLDG_TYPE_CHOICES = [
        ('Academic', 'Academic'),
        ('StudentCenter', 'Student Center'),
        # Add other types as needed
    ]
    bldg_name = models.CharField(max_length=50)
    bldg_type = models.CharField(max_length=15, choices=BLDG_TYPE_CHOICES)

    def __str__(self):
        return self.bldg_name
# Room Model
class Room(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    room_no = models.CharField(max_length=10)

    def __str__(self):
        return self.building.bldg_name+' '+str(self.room_no).rjust(3, '0')

    class Meta:
        ordering = ['building__bldg_name', 'room_no']
# Lab Model
class Lab(models.Model):
    room = models.OneToOneField(Room, on_delete=models.CASCADE, primary_key=True)
    no_of_workstations = models.IntegerField()

    def __str__(self):
        return self.room.building.bldg_name+' '+self.room.room_no

# Lecture Model
class Lecture(models.Model):
    room = models.OneToOneField(Room, on_delete=models.CASCADE, primary_key=True)
    no_of_seats = models.IntegerField()

    def __str__(self):
        return self.room.building.bldg_name+' '+self.room.room_no

# Semester Model
class Semester(models.Model):
    semester_name = models.CharField(max_length=20)
    semester_year = models.IntegerField()
    start_date = models.DateField(default='2000-01-01')
    end_date = models.DateField(default='2000-01-01')

    def __str__(self):
        return self.semester_name

# Class Model (CourseSection)
class CourseSection(models.Model):
    crn = models.CharField(max_length=10, primary_key=True)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    #faculty must have department in departments that is in Course.department
    faculty = models.ForeignKey('Faculty', on_delete=models.SET_NULL, null=True)
    timeslot = models.ForeignKey('Timeslot', on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True)
    available_seats = models.IntegerField()

    def __str__(self):
        return self.course.course_name+' | CRN: '+str(self.crn)

    def save(self, *args, **kwargs):
        if not self.crn:
            # Generate a unique crn not already in the database
            while True:
                crn = random.randint(10000, 99999)
                if not CourseSection.objects.filter(crn=crn).exists():
                    self.crn = crn
                    break

        super(CourseSection, self).save(*args, **kwargs)

@receiver(post_save, sender=CourseSection)
def create_faculty_history(sender, instance, created, **kwargs):
    if created:
        FacultyHistory.objects.create(
            faculty=instance.faculty,
            section=instance,
            semester=instance.semester
        )
        #find faculty and update num_of_courses
        if instance.faculty.fac_type == 'FullTime':
            Faculty_FullTime.objects.filter(faculty=instance.faculty).update(num_of_courses=F('num_of_courses')+1)
        else:
            Faculty_PartTime.objects.filter(faculty=instance.faculty).update(num_of_courses=F('num_of_courses')+1)
    else:
        FacultyHistory.objects.filter(
            faculty=instance.faculty,
            section=instance,
            semester=instance.semester
        ).update()

        if instance.faculty.fac_type == 'FullTime':
            Faculty_FullTime.objects.filter(faculty=instance.faculty).update(num_of_courses=F('num_of_courses')+1)
        else:
            Faculty_PartTime.objects.filter(faculty=instance.faculty).update(num_of_courses=F('num_of_courses')+1)

@receiver(post_delete, sender=CourseSection)
def delete_faculty_history(sender, instance, **kwargs):
    try:
        fh = FacultyHistory.objects.filter(
            faculty=instance.faculty,
            section=instance,
            semester=instance.semester
        )
        fh.delete()

        if instance.faculty.fac_type == 'FullTime':
            Faculty_FullTime.objects.filter(faculty=instance.faculty).update(num_of_courses=F('num_of_courses')-1)
        else:
            Faculty_PartTime.objects.filter(faculty=instance.faculty).update(num_of_courses=F('num_of_courses')-1)
    except:
        pass
# Course Model
class Course(models.Model):
    COURSE_TYPE_CHOICES = [
        ('UnderGrad', 'Undergraduate'),
        ('Grad', 'Graduate'),
    ]
    course_id = models.IntegerField(primary_key=True)
    course_number = models.IntegerField()
    course_name = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)
    no_of_credits = models.IntegerField()
    description = models.TextField()
    course_type = models.CharField(max_length=10, choices=COURSE_TYPE_CHOICES)

    def __str__(self):
        return self.course_name
    def save(self, *args, **kwargs):
        if not self.course_id:
            # Generate a unique course_id not already in the database
            while True:
                course_id = random.randint(10000, 99999)
                if not Course.objects.filter(course_id=course_id).exists():
                    self.course_id = course_id
                    break

        super(Course, self).save(*args, **kwargs)
# CoursePrereq Model
class CoursePrereq(models.Model):
    course = models.ForeignKey(Course, related_name='course', on_delete=models.CASCADE)
    pr_course = models.ForeignKey(Course, related_name='pr_course', on_delete=models.CASCADE)
    min_grade = models.CharField(max_length=2)
    date_of_last_update = models.DateField()

    def __str__(self):
        return self.course.course_name+' - '+self.pr_course.course_name
# Enrollment Model
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE)
    grade = models.CharField(max_length=2, null=True,blank=True)
    date_of_enrollment = models.DateField()

    def __str__(self):
        return self.student.user.first_name + ' ' + self.student.user.last_name+' - '+self.section.course.course_name + ' : '+str(self.grade)

@receiver(post_save, sender=Enrollment)
def create_student_history(sender, instance, created, **kwargs):
    if created:
        StudentHistory.objects.create(
            student=instance.student,
            section=instance.section,
            # course=instance.section.course,
            semester=instance.section.semester,
            grade=instance.grade
        )
    else:
        StudentHistory.objects.filter(
            student=instance.student,
            section=instance.section,
            # course=instance.section.course,
            semester=instance.section.semester
        ).update(grade=instance.grade)

#when enrollment is deleted, delete student history but only if grade is NA
@receiver(post_delete, sender=Enrollment)
def delete_student_history(sender, instance, **kwargs):
    sh = StudentHistory.objects.filter(
        student=instance.student,
        section=instance.section,
        # course=instance.section.course,
        semester=instance.section.semester
    )
    if instance.grade == 'NA' or instance.grade == None:
        sh.delete()
    else:
        return


# StudentHistory Model
class StudentHistory(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE)
    # course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    grade = models.CharField(max_length=2)

    def __str__(self):
        return self.student.user.first_name + ' ' + self.student.user.last_name+' - '+self.section.course.course_name + ' : '+self.grade

@receiver(post_delete, sender=StudentHistory)
def delete_student_history(sender, instance, **kwargs):
    Enrollment.objects.filter(
        student=instance.student,
        section=instance.section,
        id=instance.id
    ).delete()


# FacultyHistory Model
class FacultyHistory(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    def __str__(self):
        return self.faculty.user.first_name + ' ' + self.faculty.user.last_name+' - '+self.section.course.course_name


# Attendance Model
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE)
    # course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_of_class = models.DateField()
    present = models.BooleanField()

    def __str__(self):
        return str(self.date_of_class)+': '+self.student.user.first_name + ' ' + self.student.user.last_name+' - '+self.section.course.course_name + ' - Present:'+str(self.present)

# Hold Model
class Hold(models.Model):
    HOLD_TYPE_CHOICES = [
        ('Financial', 'Financial'),
        ('Academic', 'Academic'),
        ('Health', 'Health'),
        ('Disciplinary', 'Disciplinary'),
        # Add other types as needed
    ]
    hold_type = models.CharField(max_length=15, choices=HOLD_TYPE_CHOICES)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    def __str__(self):
        return self.student.user.first_name + ' ' + self.student.user.last_name+' - '+self.hold_type

# Timeslot Model
class Timeslot(models.Model):
    days = models.ManyToManyField('Day')
    periods = models.ManyToManyField('Period')

    def __str__(self):
        #convert days to M,T,W,R,F and append period times
        days_str = ''
        periods_str = ''

        for day in self.days.all():
            if day.weekday == 'Thursday':
                days_str += 'TH '
            else:
                days_str += day.weekday[0]+' '
        for period in self.periods.all():
            #convert time to 12 hour format AM or PM
            # For start time
            if period.start_time.hour >= 12:
                start_hour = period.start_time.hour if period.start_time.hour < 13 else period.start_time.hour - 12
                start_ampm = 'PM'
            else:
                start_hour = period.start_time.hour if period.start_time.hour != 0 else 12
                start_ampm = 'AM'

            # For end time
            if period.end_time.hour >= 12:
                end_hour = period.end_time.hour if period.end_time.hour < 13 else period.end_time.hour - 12
                end_ampm = 'PM'
            else:
                end_hour = period.end_time.hour if period.end_time.hour != 0 else 12
                end_ampm = 'AM'

            #convert minutes to 2 digits
            if period.start_time.minute < 10:
                start_minute = '0'+str(period.start_time.minute)
            else:
                start_minute = str(period.start_time.minute)
            if period.end_time.minute < 10:
                end_minute = '0'+str(period.end_time.minute)
            else:
                end_minute = str(period.end_time.minute)

            periods_str += str(start_hour)+':'+str(start_minute)+' '+start_ampm+' - '+str(end_hour)+':'+str(end_minute)+' '+end_ampm+' '
        return days_str+' '+periods_str

# TimeSlotDay Model (Not needed if using ManyToMany in Timeslot)
# TimeSlotPeriod Model (Not needed if using ManyToMany in Timeslot)

# Day Model
class Day(models.Model):
    weekday = models.CharField(max_length=10)

    def __str__(self):
        return self.weekday
# Period Model
class Period(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return str(self.start_time)+' - '+str(self.end_time)

class MajorDegreeRequirements(models.Model):
    major = models.ForeignKey(Major, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course,blank=True, related_name='major_courses')
    credits_required = models.IntegerField()

    def __str__(self):
        return self.major.major_name

class MinorDegreeRequirements(models.Model):
    minor = models.ForeignKey(Minor, on_delete=models.CASCADE)
    courses = models.ManyToManyField(Course, blank=True, related_name='minor_courses')
    credits_required = models.IntegerField()

    def __str__(self):
        return self.minor.minor_name