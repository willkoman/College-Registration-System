from django.core.management.base import BaseCommand
from faker import Faker
import sys
from registration.models import User, Login, Admin,Grad_Full_Time,Grad_Part_Time,Undergrad_Full_Time,Undergrad_Part_Time,Graduate,Undergraduate, Student, Faculty, Major, Minor, Department, Building, Room, Course, CourseSection, Semester, Timeslot

class Command(BaseCommand):
    help = 'Generate random data'

    def handle(self, *args, **kwargs):
        fake = Faker()
        departmentList = {
            'Math':'MAT',
            'Science':'SCI',
            'Arts':'ART',
            'English':'ELA',
            'History':'HIS',
            'Computer Science':'CS',
            'Business':'BS',
            'Engineering':'ENG',
            'Music':'MUS',
            'Theater':'THE',
            'Dance':'DAN',
            'Biology':'BIO',
            'Chemistry':'CHE',
            'Physics':'PHY',
            'Geology':'GEO',
            'Psychology':'PSY',
            'Sociology':'SOC',
            'Anthropology':'ANT',
            'Philosophy':'PHI',
            'Religion':'REL',
            'Economics':'ECO',
            'Political Science':'POL',
            'Foreign Language':'FOR',
            'Education':'EDU',
            'Nursing':'NUR',
            'Medicine':'MED',
            'Law':'LAW',
            'Criminal Justice':'CRJ',
            'Architecture':'ARC',
            'Agriculture':'AGR',
            'Veterinary Medicine':'VET',
            'Dentistry':'DEN',
            'Pharmacy':'PHA',
            'Library Science':'LIB',
            'Journalism':'JOU',
            'Communications':'COM',
            'Public Relations':'PUR',
            'Social Work':'SCW',
            'Public Administration':'PAD',
            'Urban Planning':'URB',
            'Hospitality':'HOS',
            'Recreation':'REC',
            'Fitness':'FIT',
            'Cosmetology':'COS',
            'Culinary Arts':'CUL',
            'Other':'Misc'
        }
        majorList = ['Math', 'Science', 'Arts', 'English', 'History', 'Computer Science', 'Business', 'Engineering', 'Music', 'Theater', 'Dance', 'Biology', 'Chemistry', 'Physics', 'Geology', 'Psychology', 'Sociology', 'Anthropology', 'Philosophy', 'Religion', 'Economics', 'Political Science', 'Foreign Language', 'Education', 'Nursing', 'Medicine', 'Law', 'Criminal Justice', 'Architecture', 'Agriculture', 'Veterinary Medicine', 'Dentistry', 'Pharmacy', 'Library Science', 'Journalism', 'Communications', 'Public Relations', 'Social Work', 'Public Administration', 'Urban Planning', 'Hospitality', 'Recreation', 'Fitness', 'Cosmetology', 'Culinary Arts', 'Undecided']
        # Generate Departments
        for department_name, department_id in departmentList.items():
            Department.objects.get_or_create(
                department_id=department_id,
                department_name=department_name,
                email=fake.email(),
                phone=fake.unique.random_number(digits=10),
            )


        # Generate Majors
        for _ in range(len(majorList)):
            Major.objects.get_or_create(
                major_name=majorList[_],
                department=Department.objects.filter(department_name=majorList[_]).first(),
            )

        # Generate Minors
        for _ in range(len(majorList)):
            Minor.objects.get_or_create(
                minor_name=majorList[_],
                department=Department.objects.filter(department_name=majorList[_]).first(),
            )

