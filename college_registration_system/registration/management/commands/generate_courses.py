from django.core.management.base import BaseCommand
from faker import Faker
import sys
from registration.models import User, Login, Admin,Grad_Full_Time,Grad_Part_Time,Undergrad_Full_Time,Undergrad_Part_Time,Graduate,Undergraduate, Student, Faculty, Major, Minor, Department, Building, Room, Course, CourseSection, Semester, Timeslot

class Command(BaseCommand):
    help = 'Generate random data'

    def handle(self, *args, **kwargs):
        fake = Faker()
        course_name_prefixes = ['Intro to', 'Fundamentals of', 'Concepts of']

        # Generate Courses
        for _ in range(50):
            try:
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
            except:
                pass

        for _ in range(50):
            try:
                CourseSection.objects.get_or_create(
                    crn=fake.unique.random_number(digits=5),
                    course=Course.objects.order_by('?').first(),
                    faculty=Faculty.objects.order_by('?').first(),
                    timeslot=Timeslot.objects.order_by('?').first(),
                    room=Room.objects.order_by('?').first(),
                    semester=Semester.objects.order_by('?').first(),
                    available_seats=fake.random_int(min=1, max=50),
                )
            except:
                pass
