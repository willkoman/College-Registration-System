from django.core.management.base import BaseCommand
from faker import Faker
import sys
from registration.models import User, Login, Admin,Grad_Full_Time,Grad_Part_Time,Undergrad_Full_Time,Undergrad_Part_Time,Graduate,Undergraduate, Student, Faculty, Major, Minor, Department, Building, Room, Course, CourseSection, Semester, Timeslot

class Command(BaseCommand):
    help = 'Generate random data'

    def handle(self, *args, **kwargs):
        fake = Faker()

        for _ in range(20):
            try:
                # Create or get User
                user, user_created = User.objects.get_or_create(
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    defaults={
                        'gender': fake.random_element(['M', 'F', 'O']),
                        'dob': fake.date_of_birth(),
                        'street': fake.street_address(),
                        'city': fake.city(),
                        'state': fake.state(),
                        'zip_code': fake.zipcode(),
                        'user_type': fake.random_element(['Student', 'Faculty']),
                    }
                )

                if user.user_type == 'Student':
                    student, student_created = Student.objects.get_or_create(
                        user=user,
                        defaults={
                            'major_id': Major.objects.order_by('?').first(),
                            'enrollment_year': fake.random_int(min=1, max=4),
                            'student_type': fake.random_element(['Undergraduate', 'Graduate']),
                        }
                    )
                    if not student_created:
                        # Update attributes if the student already exists
                        student.major_id = Major.objects.order_by('?').first()
                        student.enrollment_year = fake.random_int(min=1, max=4)
                        student.student_type = fake.random_element(['Undergraduate', 'Graduate'])
                        student.save()

                    if student.student_type == 'Undergraduate':
                        print("\tcreating Undergraduate:", student)  # Debugging line
                        undergrad, undergrad_created = Undergraduate.objects.get_or_create(
                            student=student,
                            defaults={
                                'Department': Department.objects.order_by('?').first(),
                                'undergrad_student_type': fake.random_element(['FullTime', 'PartTime']),
                            }# Debugging line
                        )
                        if not undergrad_created:
                            print("\tupdating Undergraduate:", undergrad)  # Debugging line
                            # Update attributes if the undergraduate already exists
                            undergrad.department = Department.objects.order_by('?').first()
                            undergrad.undergrad_student_type = fake.random_element(['FullTime', 'PartTime'])
                            undergrad.save()
                            print("\t\tundergrad type:", undergrad.undergrad_student_type)

                        if undergrad.undergrad_student_type == 'FullTime':
                            print("\t\tcreating FullTime:", undergrad)
                            undergrad_fulltime, undergrad_fulltime_created = Undergrad_Full_Time.objects.get_or_create(
                                student=undergrad,
                                defaults={
                                    'standing' : fake.random_element(['Freshman', 'Sophomore', 'Junior', 'Senior']),
                                    'creds_earned' : fake.random_int(min=4, max=30),
                                }
                            )
                            if not undergrad_fulltime_created:
                                print("\t\tupdating FullTime:", undergrad_fulltime)
                                undergrad_fulltime.standing = fake.random_element(['Freshman', 'Sophomore', 'Junior', 'Senior'])
                                undergrad_fulltime.creds_earned = fake.random_int(min=4, max=30)
                                undergrad_fulltime.save()

                        elif undergrad.undergrad_student_type == 'PartTime':
                            print("\t\tcreating PartTime:", undergrad)
                            undergrad_parttime, undergrad_parttime_created = Undergrad_Part_Time.objects.get_or_create(
                                student=undergrad,
                                defaults={
                                    'standing' : fake.random_element(['Freshman', 'Sophomore', 'Junior', 'Senior']),
                                    'creds_earned' : fake.random_int(min=4, max=30),
                                }
                            )
                            if not undergrad_parttime_created:
                                print("\t\tupdating PartTime:", undergrad_parttime)
                                undergrad_parttime.standing = fake.random_element(['Freshman', 'Sophomore', 'Junior', 'Senior'])
                                undergrad_parttime.creds_earned = fake.random_int(min=4, max=30)
                                undergrad_parttime.save()

                    elif student.student_type == 'Graduate':
                        print("\tcreating Graduate:", student)
                        grad, grad_created = Graduate.objects.get_or_create(

                            student=student,
                            defaults={
                                'Department': Department.objects.order_by('?').first(),
                                'Program': fake.random_element(['Masters', 'PhD']),
                                'grad_student_type': fake.random_element(['FullTime', 'PartTime']),
                            }
                        )
                        if not grad_created:
                            print("\tupdating Graduate:", student)  # Debugging line
                            # Update attributes if the graduate already exists
                            grad.department = Department.objects.order_by('?').first()
                            grad.program = fake.random_element(['Masters', 'PhD'])
                            grad.grad_student_type = fake.random_element(['FullTime', 'PartTime'])
                            grad.save()
                            print("\t\tgrad type:", grad.grad_student_type)

                        if grad.grad_student_type == 'FullTime':
                            print("\t\tcreating FullTime:", grad)
                            grad_fulltime, grad_fulltime_created = Grad_Full_Time.objects.get_or_create(
                                student=grad,
                                defaults={
                                    'credits_earned' : fake.random_int(min=50, max=90),
                                    'thesis' : fake.boolean(),
                                    'qualifying_exam' : fake.boolean(),
                                }
                            )
                            if not grad_fulltime_created:
                                print("\t\tupdating FullTime:", grad_fulltime)
                                grad_fulltime.credits_earned = fake.random_int(min=50, max=90)
                                grad_fulltime.thesis = fake.boolean()
                                grad_fulltime.qualifying_exam = fake.boolean()
                                grad_fulltime.save()

                        elif grad.grad_student_type == 'PartTime':
                            print("\t\tcreating PartTime:", grad)
                            grad_parttime, grad_parttime_created = Grad_Part_Time.objects.get_or_create(
                                student=grad,
                                defaults={
                                    'credits_earned' : fake.random_int(min=50, max=90),
                                    'thesis' : fake.boolean(),
                                    'qualifying_exam' : fake.boolean(),
                                }
                            )
                            if not grad_parttime_created:
                                print("\t\tupdating PartTime:", grad_parttime)
                                grad_parttime.credits_earned = fake.random_int(min=50, max=90)
                                grad_parttime.thesis = fake.boolean()
                                grad_parttime.qualifying_exam = fake.boolean()
                                grad_parttime.save()


                elif user.user_type == 'Faculty':
                    print("\tcreating Faculty:", user)  # Debugging line
                    faculty, faculty_created = Faculty.objects.get_or_create(
                        user=user,
                        defaults={
                            'rank': fake.random_element(['Prof', 'AsstProf', 'Adjunct', 'TA']),
                            'department': Department.objects.order_by('?').first(),
                            'specialty': fake.random_element(['Math', 'Science', 'Arts']),
                            'fac_type': fake.random_element(['FT', 'PT']),
                        }
                    )
                    if not faculty_created:
                        print("\tupdating Faculty:", faculty)
                        # Update attributes if the faculty already exists
                        faculty.rank = fake.random_element(['Prof', 'AsstProf', 'Adjunct', 'TA'])
                        faculty.department = Department.objects.order_by('?').first()
                        faculty.specialty = fake.random_element(['Math', 'Science', 'Arts'])
                        faculty.fac_type = fake.random_element(['FT', 'PT'])
                        faculty.save()
            except:
                print("Unexpected error:", sys.exc_info())