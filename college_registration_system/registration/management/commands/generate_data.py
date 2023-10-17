from django.core.management.base import BaseCommand
from faker import Faker
import sys
from registration.models import User, Login, Admin,Grad_Full_Time,Grad_Part_Time,Undergrad_Full_Time,Undergrad_Part_Time,Graduate,Undergraduate, Student, Faculty, Major, Minor, Department, Building, Room, Course, CourseSection, Semester, Timeslot

class Command(BaseCommand):
    help = 'Generate random data'

    def handle(self, *args, **kwargs):
        fake = Faker()
    #     departmentList = {
    #         'Math':'MAT',
    #         'Science':'SCI',
    #         'Arts':'ART',
    #         'English':'ELA',
    #         'History':'HIS',
    #         'Computer Science':'CS',
    #         'Business':'BS',
    #         'Engineering':'ENG',
    #         'Music':'MUS',
    #         'Theater':'THE',
    #         'Dance':'DAN',
    #         'Biology':'BIO',
    #         'Chemistry':'CHE',
    #         'Physics':'PHY',
    #         'Geology':'GEO',
    #         'Psychology':'PSY',
    #         'Sociology':'SOC',
    #         'Anthropology':'ANT',
    #         'Philosophy':'PHI',
    #         'Religion':'REL',
    #         'Economics':'ECO',
    #         'Political Science':'POL',
    #         'Foreign Language':'FOR',
    #         'Education':'EDU',
    #         'Nursing':'NUR',
    #         'Medicine':'MED',
    #         'Law':'LAW',
    #         'Criminal Justice':'CRJ',
    #         'Architecture':'ARC',
    #         'Agriculture':'AGR',
    #         'Veterinary Medicine':'VET',
    #         'Dentistry':'DEN',
    #         'Pharmacy':'PHA',
    #         'Library Science':'LIB',
    #         'Journalism':'JOU',
    #         'Communications':'COM',
    #         'Public Relations':'PUR',
    #         'Social Work':'SCW',
    #         'Public Administration':'PAD',
    #         'Urban Planning':'URB',
    #         'Hospitality':'HOS',
    #         'Recreation':'REC',
    #         'Fitness':'FIT',
    #         'Cosmetology':'COS',
    #         'Culinary Arts':'CUL',
    #         'Other':'Misc'
    #     }
    #     majorList = ['Math', 'Science', 'Arts', 'English', 'History', 'Computer Science', 'Business', 'Engineering', 'Music', 'Theater', 'Dance', 'Biology', 'Chemistry', 'Physics', 'Geology', 'Psychology', 'Sociology', 'Anthropology', 'Philosophy', 'Religion', 'Economics', 'Political Science', 'Foreign Language', 'Education', 'Nursing', 'Medicine', 'Law', 'Criminal Justice', 'Architecture', 'Agriculture', 'Veterinary Medicine', 'Dentistry', 'Pharmacy', 'Library Science', 'Journalism', 'Communications', 'Public Relations', 'Social Work', 'Public Administration', 'Urban Planning', 'Hospitality', 'Recreation', 'Fitness', 'Cosmetology', 'Culinary Arts', 'Undecided']
    #     # Generate Departments
    #     for department_name, department_id in departmentList.items():
    #         Department.objects.get_or_create(
    #             department_id=department_id,
    #             department_name=department_name,
    #             email=fake.email(),
    #             phone=fake.unique.random_number(digits=10),
    #         )


    #     # Generate Majors
    #     for _ in range(len(majorList)):
    #         Major.objects.get_or_create(
    #             major_name=majorList[_],
    #             department=Department.objects.filter(department_name=majorList[_]).first(),
    #         )

    #     # Generate Minors
    #     for _ in range(len(majorList)):
    #         Minor.objects.get_or_create(
    #             minor_name=majorList[_],
    #             department=Department.objects.filter(department_name=majorList[_]).first(),
    #         )


    # #     '''
    # #     # Course Model
    # #     class Course(models.Model):
    # #         COURSE_TYPE_CHOICES = [
    # #             ('UnderGrad', 'Undergraduate'),
    # #             ('Grad', 'Graduate'),
    # #         ]
    # #         course_id = models.IntegerField(primary_key=True)
    # #         course_number = models.IntegerField(max_length=4)
    # #         course_name = models.CharField(max_length=50)
    # #         department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)
    # #         no_of_credits = models.IntegerField()
    # #         description = models.TextField()
    # #         course_type = models.CharField(max_length=10, choices=COURSE_TYPE_CHOICES)
    # # '''
        course_name_prefixes = ['Intro to', 'Fundamentals of', 'Concepts of']

        # Generate Courses
        for _ in range(50):
            # Randomly select a department
            random_department = Department.objects.order_by('?').first()

            # Generate a course name based on the department name
            course_name = f"{fake.random_element(course_name_prefixes)} {random_department.department_name}"

            Course.objects.get_or_create(
                course_id=fake.unique.random_number(digits=5),
                course_number=fake.random_number(digits=4),
                course_name=course_name,
                department=random_department,
                no_of_credits=fake.random_int(min=1, max=4),
                description=fake.text(),
                course_type=fake.random_element(['UnderGrad', 'Grad']),
            )


    #     '''
    #     crn = models.CharField(max_length=10, primary_key=True)
    #     course = models.ForeignKey('Course', on_delete=models.CASCADE)
    #     faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True)
    #     timeslot = models.ForeignKey('Timeslot', on_delete=models.SET_NULL, null=True)
    #     room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)
    #     semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True)
    #     available_seats
    # '''
    #     #Generate Course Sections
        for _ in range(50):
            CourseSection.objects.get_or_create(
                crn=fake.unique.random_number(digits=5),
                course=Course.objects.order_by('?').first(),
                faculty=Faculty.objects.order_by('?').first(),
                timeslot=Timeslot.objects.order_by('?').first(),
                room=Room.objects.order_by('?').first(),
                semester=Semester.objects.order_by('?').first(),
                available_seats=fake.random_int(min=1, max=50),
            )

        # for _ in range(20):
        #     try:
        #         # Create or get User
        #         user, user_created = User.objects.get_or_create(
        #             first_name=fake.first_name(),
        #             last_name=fake.last_name(),
        #             defaults={
        #                 'gender': fake.random_element(['M', 'F', 'O']),
        #                 'dob': fake.date_of_birth(),
        #                 'street': fake.street_address(),
        #                 'city': fake.city(),
        #                 'state': fake.state(),
        #                 'zip_code': fake.zipcode(),
        #                 'user_type': fake.random_element(['Student', 'Faculty']),
        #             }
        #         )

        #         if user.user_type == 'Student':
        #             student, student_created = Student.objects.get_or_create(
        #                 user=user,
        #                 defaults={
        #                     'major_id': Major.objects.order_by('?').first(),
        #                     'enrollment_year': fake.random_int(min=1, max=4),
        #                     'student_type': fake.random_element(['Undergraduate', 'Graduate']),
        #                 }
        #             )
        #             if not student_created:
        #                 # Update attributes if the student already exists
        #                 student.major_id = Major.objects.order_by('?').first()
        #                 student.enrollment_year = fake.random_int(min=1, max=4)
        #                 student.student_type = fake.random_element(['Undergraduate', 'Graduate'])
        #                 student.save()

        #             if student.student_type == 'Undergraduate':
        #                 print("\tcreating Undergraduate:", student)  # Debugging line
        #                 undergrad, undergrad_created = Undergraduate.objects.get_or_create(
        #                     student=student,
        #                     defaults={
        #                         'Department': Department.objects.order_by('?').first(),
        #                         'undergrad_student_type': fake.random_element(['FullTime', 'PartTime']),
        #                     }# Debugging line
        #                 )
        #                 if not undergrad_created:
        #                     print("\tupdating Undergraduate:", undergrad)  # Debugging line
        #                     # Update attributes if the undergraduate already exists
        #                     undergrad.department = Department.objects.order_by('?').first()
        #                     undergrad.undergrad_student_type = fake.random_element(['FullTime', 'PartTime'])
        #                     undergrad.save()
        #                     print("\t\tundergrad type:", undergrad.undergrad_student_type)

        #                 if undergrad.undergrad_student_type == 'FullTime':
        #                     print("\t\tcreating FullTime:", undergrad)
        #                     undergrad_fulltime, undergrad_fulltime_created = Undergrad_Full_Time.objects.get_or_create(
        #                         student=undergrad,
        #                         defaults={
        #                             'standing' : fake.random_element(['Freshman', 'Sophomore', 'Junior', 'Senior']),
        #                             'creds_earned' : fake.random_int(min=4, max=30),
        #                         }
        #                     )
        #                     if not undergrad_fulltime_created:
        #                         print("\t\tupdating FullTime:", undergrad_fulltime)
        #                         undergrad_fulltime.standing = fake.random_element(['Freshman', 'Sophomore', 'Junior', 'Senior'])
        #                         undergrad_fulltime.creds_earned = fake.random_int(min=4, max=30)
        #                         undergrad_fulltime.save()

        #                 elif undergrad.undergrad_student_type == 'PartTime':
        #                     print("\t\tcreating PartTime:", undergrad)
        #                     undergrad_parttime, undergrad_parttime_created = Undergrad_Part_Time.objects.get_or_create(
        #                         student=undergrad,
        #                         defaults={
        #                             'standing' : fake.random_element(['Freshman', 'Sophomore', 'Junior', 'Senior']),
        #                             'creds_earned' : fake.random_int(min=4, max=30),
        #                         }
        #                     )
        #                     if not undergrad_parttime_created:
        #                         print("\t\tupdating PartTime:", undergrad_parttime)
        #                         undergrad_parttime.standing = fake.random_element(['Freshman', 'Sophomore', 'Junior', 'Senior'])
        #                         undergrad_parttime.creds_earned = fake.random_int(min=4, max=30)
        #                         undergrad_parttime.save()

        #             elif student.student_type == 'Graduate':
        #                 print("\tcreating Graduate:", student)
        #                 grad, grad_created = Graduate.objects.get_or_create(

        #                     student=student,
        #                     defaults={
        #                         'Department': Department.objects.order_by('?').first(),
        #                         'Program': fake.random_element(['Masters', 'PhD']),
        #                         'grad_student_type': fake.random_element(['FullTime', 'PartTime']),
        #                     }
        #                 )
        #                 if not grad_created:
        #                     print("\tupdating Graduate:", student)  # Debugging line
        #                     # Update attributes if the graduate already exists
        #                     grad.department = Department.objects.order_by('?').first()
        #                     grad.program = fake.random_element(['Masters', 'PhD'])
        #                     grad.grad_student_type = fake.random_element(['FullTime', 'PartTime'])
        #                     grad.save()
        #                     print("\t\tgrad type:", grad.grad_student_type)

        #                 if grad.grad_student_type == 'FullTime':
        #                     print("\t\tcreating FullTime:", grad)
        #                     grad_fulltime, grad_fulltime_created = Grad_Full_Time.objects.get_or_create(
        #                         student=grad,
        #                         defaults={
        #                             'credits_earned' : fake.random_int(min=50, max=90),
        #                             'thesis' : fake.boolean(),
        #                             'qualifying_exam' : fake.boolean(),
        #                         }
        #                     )
        #                     if not grad_fulltime_created:
        #                         print("\t\tupdating FullTime:", grad_fulltime)
        #                         grad_fulltime.credits_earned = fake.random_int(min=50, max=90)
        #                         grad_fulltime.thesis = fake.boolean()
        #                         grad_fulltime.qualifying_exam = fake.boolean()
        #                         grad_fulltime.save()

        #                 elif grad.grad_student_type == 'PartTime':
        #                     print("\t\tcreating PartTime:", grad)
        #                     grad_parttime, grad_parttime_created = Grad_Part_Time.objects.get_or_create(
        #                         student=grad,
        #                         defaults={
        #                             'credits_earned' : fake.random_int(min=50, max=90),
        #                             'thesis' : fake.boolean(),
        #                             'qualifying_exam' : fake.boolean(),
        #                         }
        #                     )
        #                     if not grad_parttime_created:
        #                         print("\t\tupdating PartTime:", grad_parttime)
        #                         grad_parttime.credits_earned = fake.random_int(min=50, max=90)
        #                         grad_parttime.thesis = fake.boolean()
        #                         grad_parttime.qualifying_exam = fake.boolean()
        #                         grad_parttime.save()


        #         elif user.user_type == 'Faculty':
        #             print("\tcreating Faculty:", user)  # Debugging line
        #             faculty, faculty_created = Faculty.objects.get_or_create(
        #                 user=user,
        #                 defaults={
        #                     'rank': fake.random_element(['Prof', 'AsstProf', 'Adjunct', 'TA']),
        #                     'department': Department.objects.order_by('?').first(),
        #                     'specialty': fake.random_element(['Math', 'Science', 'Arts']),
        #                     'fac_type': fake.random_element(['FT', 'PT']),
        #                 }
        #             )
        #             if not faculty_created:
        #                 print("\tupdating Faculty:", faculty)
        #                 # Update attributes if the faculty already exists
        #                 faculty.rank = fake.random_element(['Prof', 'AsstProf', 'Adjunct', 'TA'])
        #                 faculty.department = Department.objects.order_by('?').first()
        #                 faculty.specialty = fake.random_element(['Math', 'Science', 'Arts'])
        #                 faculty.fac_type = fake.random_element(['FT', 'PT'])
        #                 faculty.save()
        #     except:
        #         print("Unexpected error:", sys.exc_info())