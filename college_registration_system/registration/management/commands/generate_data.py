import random
import uuid
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from faker import Faker
from registration.models import Building, Department, Room, Semester,CoursePrereq, Timeslot, User, Student, Faculty, Course, CourseSection, Enrollment, Major, Faculty_FullTime, Faculty_PartTime, Grad_Part_Time, Grad_Full_Time, Undergrad_Part_Time, Undergrad_Full_Time, Graduate, Undergraduate,Major,Minor,MajorDegreeRequirements,MinorDegreeRequirements
import datetime as dt
from collections import defaultdict
class Command(BaseCommand):
    help = 'Populates the database with random data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Select an option to proceed:")
        self.stdout.write("1: Generate all data")
        self.stdout.write("2: Generate rooms")
        self.stdout.write("3: Generate users")
        self.stdout.write("4: Generate courses")
        self.stdout.write("5: Generate sections")
        self.stdout.write("6: Generate enrollments")
        self.stdout.write("7: Remove underfilled sections")
        self.stdout.write("8: Generate major and minor requirements")

        choice = input("Enter your choice (1-8): ")

        fake = Faker()

        if choice == '1':
            self.create_rooms(fake)
            self.create_users(fake)
            self.create_courses(fake)
            self.create_sections(fake)
            self.enroll_students(fake)
            self.remove_underfilled_sections(fake)
            self.create_major_minor_requirements(fake)
        elif choice == '2':
            self.create_rooms(fake)
        elif choice == '3':
            self.create_users(fake)
        elif choice == '4':
            self.create_courses(fake)
        elif choice == '5':
            self.create_sections(fake)
        elif choice == '6':
            self.enroll_students(fake)
        elif choice == '7':
            self.remove_underfilled_sections(fake)
        elif choice == '8':
            self.create_major_minor_requirements(fake)
        else:
            self.stdout.write("Invalid choice.")

    def create_rooms(self, fake):
        for building in Building.objects.all():
            lowerbound=int(input(f'Enter the lower bound for rooms in {building}: '))
            upperbound=int(input(f'Enter the upper bound for rooms in {building}: '))
            for i in range(lowerbound,upperbound):
                room, created = Room.objects.get_or_create(building=building, room_no=f'{i+1}')
                if created:
                    print(f'Created room {room} in {building}')
                else:
                    print(f'Room {room} in {building} already exists')

    def create_users(self, fake):
        for _ in range(200):

            user = User.objects.create(
                id=uuid.uuid4(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                gender=random.choice(['M', 'F']),
                dob=fake.date_of_birth(),
                street=fake.street_address(),
                city=fake.city(),
                state=fake.state(),
                zip_code=fake.zipcode(),
                user_type='Student'
            )
            user.save()
            s=Student.objects.get(user=user)
            s.student_type=random.choice(['Undergraduate', 'Graduate'])
            s.major_id=Major.objects.order_by('?').first()
            s.enrollment_year=fake.random_int(min=2015, max=2020)
            # s.studentID=fake.unique.random_int(min=7000005, max=7999999)
            s.save()
            print(f'Created student {user.first_name} {user.last_name} with id {s.studentID}')

        for _ in range(50):
            user = User.objects.create(
                id=uuid.uuid4(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                gender=random.choice(['M', 'F']),
                dob=fake.date_of_birth(),
                street=fake.street_address(),
                city=fake.city(),
                state=fake.state(),
                zip_code=fake.zipcode(),
                user_type='Faculty'
            )
            user.save()
            f=Faculty.objects.get_or_create(
            user=user,
            fac_type=random.choice(['FullTime', 'PartTime']),
            specialty=fake.job(),
            rank=random.choice(['Professor', 'Assistant Professor', 'Adjunct Professor', 'Teaching Assistant']),

            )[0]
            f.departments.add(Department.objects.order_by('?').first())
            f.save()

            print(f'Created faculty {user.first_name} {user.last_name} with type {f.fac_type} and rank {f.rank}')
        for undergrads in Undergraduate.objects.all():
            undergrads.undergrad_student_type = random.choice(['FullTime', 'PartTime'])
            undergrads.department = Student.objects.get(user=undergrads.student.user).major_id.department
            print(f"Undergrad {undergrads.student.user.first_name} {undergrads.student.user.last_name} is in department {undergrads.department}")
            undergrads.save()
        for grads in Graduate.objects.all():
            grads.grad_student_type = random.choice(['FullTime', 'PartTime'])
            grads.department = Student.objects.get(user=grads.student.user).major_id.department
            print(f"Grad {grads.student.user.first_name} {grads.student.user.last_name} is in department {grads.department}")
            grads.save()
        for fulltimes in Grad_Full_Time.objects.all():
            fulltimes.credits_earned = fake.random_int(min=0, max=30)
            fulltimes.qualifying_exam = random.choice([True, False])
            fulltimes.thesis = random.choice([True, False])
            fulltimes.year = fake.random_int(min=2015, max=2020)
            print(f"Fulltime Grad {fulltimes.student.student.user.first_name} {fulltimes.student.student.user.last_name} is in year {fulltimes.year}")
            fulltimes.save()
        for parttimes in Grad_Part_Time.objects.all():
            parttimes.credits_earned = fake.random_int(min=0, max=30)
            parttimes.qualifying_exam = random.choice([True, False])
            parttimes.thesis = random.choice([True, False])
            parttimes.year = fake.random_int(min=2015, max=2020)
            print(f"Parttime Grad {parttimes.student.student.user.first_name} {parttimes.student.student.user.last_name} is in year {parttimes.year}")
            parttimes.save()
        for fulltimes in Undergrad_Full_Time.objects.all():
            fulltimes.creds_earned = fake.random_int(min=0, max=30)
            fulltimes.standing = random.choice(['Freshman', 'Sophomore', 'Junior', 'Senior'])
            print(f"Fulltime Undergrad {fulltimes.student.student.user.first_name} {fulltimes.student.student.user.last_name} is in year {fulltimes.standing}")
            fulltimes.save()
        for parttimes in Undergrad_Part_Time.objects.all():
            parttimes.creds_earned = fake.random_int(min=0, max=30)
            parttimes.standing = random.choice(['Freshman', 'Sophomore', 'Junior', 'Senior'])
            print(f"Parttime Undergrad {parttimes.student.student.user.first_name} {parttimes.student.student.user.last_name} is in year {parttimes.standing}")
            parttimes.save()
        #give all faculty a room. faculty_fulltime and faculty_parttime hold the room attribute
        for fulltimes in Faculty_FullTime.objects.all():
            fulltimes.office = random.choice(Room.objects.all())
            print(f"Fulltime Faculty {fulltimes.faculty.user.first_name} {fulltimes.faculty.user.last_name} is in room {fulltimes.office}")
            fulltimes.save()
        for parttimes in Faculty_PartTime.objects.all():
            parttimes.office = random.choice(Room.objects.all())
            print(f"Parttime Faculty {parttimes.faculty.user.first_name} {parttimes.faculty.user.last_name} is in room {parttimes.office}")
            parttimes.save()

    def create_courses(self, fake):

        for major in Major.objects.all():
            try:
                if major.major_name == 'Undecided':
                    continue
                for course_prefix in ['Intro to', 'Concepts of', 'Advanced Subjects of']:
                    # Create course
                    course_level = 'UnderGrad' if course_prefix != 'Advanced Subjects of' else 'Grad'
                    course, created = Course.objects.get_or_create(
                        course_id=fake.random_int(min=10000, max=99999),
                        defaults={
                            'course_name': f'{course_prefix} {major.major_name}',
                            'department': major.department,
                            'course_type': course_level,
                            'course_number': fake.random_int(min=100, max=499 if course_level == 'UnderGrad' else 899),
                            'no_of_credits': random.choice([3, 4])
                        }
                    )
                    if created:
                        print(f'Created {course.course_name}')
                    else:
                        print(f'Course {course.course_name} already exists')
            except IntegrityError:
                print(f'Course {course.course_name} already exists')
        #create prereqs for concepts of courses and advanced subjects of courses
        for course in Course.objects.all():
            if course.course_name.startswith('Concepts of') or course.course_name.startswith('Advanced Subjects of'):
                #set prereq to be lower level course in same major
                if course.course_name.startswith('Concepts of'):
                    prereq = Course.objects.filter(course_name__startswith='Intro to', department=course.department).order_by('?').first()
                elif course.course_name.startswith('Advanced Subjects of'):
                    prereq = Course.objects.filter(course_name__startswith='Concepts of', department=course.department).order_by('?').first()
                CoursePrereq.objects.create(
                    course=course,
                    pr_course=prereq,
                    min_grade='C',
                    date_of_last_update=dt.date.today()
                )
    def create_sections(self, fake):
        faculty_course_count = defaultdict(int)
        for course in Course.objects.all():
            # Create 1-2 sections for each course
            num_of_sections = random.randint(0, 2)

            for _ in range(num_of_sections):
                # Select a random faculty member who hasn't exceeded their course limit
                eligible_faculty = [f for f in Faculty.objects.all() if faculty_course_count[f.user.id] < (1 if f.fac_type == 'PartTime' else 2)]
                #if possible, only select faculty from the same department as the course
                eligible_faculty = [f for f in eligible_faculty if f.departments.filter(department_name=course.department.department_name).exists()]
                if not eligible_faculty:
                    print("No eligible faculty available for more courses.")
                    break

                selected_faculty = random.choice(eligible_faculty)

                # Create a course section with the selected faculty
                for semester in Semester.objects.all():
                    #if fall 2023 then skip
                    if semester.semester_name == 'Fall 2023':
                        continue
                    print(f'Creating section for {course.course_name} taught by {selected_faculty}')
                    CourseSection.objects.create(
                        course=course,
                        crn=fake.random_int(min=10000, max=99999),
                        available_seats=fake.random_int(min=10, max=20),
                        faculty=selected_faculty,
                        semester=semester,
                        timeslot=fake.random_element(elements=Timeslot.objects.all()),
                        room=fake.random_element(elements=Room.objects.all()),
                    )
                # Update the faculty's course count
                faculty_course_count[selected_faculty.user.id] += 1

    def enroll_students(self, fake):
        for student in Student.objects.all():
            for semester in Semester.objects.all():
                course_limit = 2 if student.student_type == 'PartTime' else 4
                available_courses = Course.objects.filter(course_type='UnderGrad') if student.student_type == 'Undergraduate' else Course.objects.all()
                print(f"Available courses for {student}: {available_courses.count()}")
                for _ in range(course_limit):
                    section = CourseSection.objects.filter(course__in=available_courses,semester=semester).order_by('?').first()
                    if section:
                        if section.enrollment_set.count() >= section.available_seats:
                            print(f'Section {section} is full! Trying again...')
                            course_limit += 1
                            continue
                        #if timeslot conflicts with another course, try again
                        if Enrollment.objects.filter(student=student, section__timeslot=section.timeslot,section__semester=section.semester).exists():
                            print(f"Section {section} conflicts with another course! Trying again...")
                            course_limit += 1
                            continue
                        Enrollment.objects.create(
                            student=student,
                            section=section,
                            grade=random.choice(['A', 'B', 'C', 'D', 'F']),
                            date_of_enrollment=dt.date.today()
                        )
                        print(f'Enrolled {student} in {section} for {semester}')
                    else:
                        print(f'No sections available for {student}!')

    def remove_underfilled_sections(self, fake):
        for section in CourseSection.objects.all():
            if section.enrollment_set.count() < 5:
                print(f'Removing section {section}')
                section.delete()

    def create_major_minor_requirements(self,fake):
        # add all courses in major to major requirements. each major has one major requirements with a many-to-many field for courses
        for major in Major.objects.all():
            major_requirements = MajorDegreeRequirements.objects.create(
                major=major,
                credits_required=120
            )
            #add all courses with major name in course name to major requirements
            for course in Course.objects.filter(course_name__contains=major.major_name):
                major_requirements.courses.add(course)
            major_requirements.save()
        #add all courses in minor to minor requirements. each minor has one minor requirements with a many-to-many field for courses
        for minor in Minor.objects.all():
            minor_requirements = MinorDegreeRequirements.objects.create(
                minor=minor,
                credits_required=60
            )
            #add all courses with minor name in course name to minor requirements
            for course in Course.objects.filter(course_name__contains=minor.minor_name):
                minor_requirements.courses.add(course)
            minor_requirements.save()

        #all requirements should have intro to: english, math, science, and social science and concepts of english, math, science, and social science as prereqs. Some will have intro to chemistry and intro to biology as prereqs
        for major in Major.objects.all():
            major_requirements = MajorDegreeRequirements.objects.get(major=major)
            #add intro to english, math, science, and social science
            major_requirements.courses.add(Course.objects.get(course_name=f'Intro to English'))
            major_requirements.courses.add(Course.objects.get(course_name=f'Intro to Math'))
            major_requirements.courses.add(Course.objects.get(course_name=f'Intro to Science'))
            major_requirements.courses.add(Course.objects.get(course_name=f'Intro to History'))
            #add concepts of english, math, science, and social science
            major_requirements.courses.add(Course.objects.get(course_name=f'Concepts of English'))
            major_requirements.courses.add(Course.objects.get(course_name=f'Concepts of Math'))
            major_requirements.courses.add(Course.objects.get(course_name=f'Concepts of Science'))
            major_requirements.courses.add(Course.objects.get(course_name=f'Concepts of History'))
            #add intro to chemistry and intro to biology if major is biology or chemistry
            if fake.random_int(min=0,max=1) == 1:
                major_requirements.courses.add(Course.objects.get(course_name=f'Intro to Chemistry'))
            else:
                major_requirements.courses.add(Course.objects.get(course_name=f'Intro to Biology'))
            major_requirements.save()

        for minor in Minor.objects.all():
            minor_requirements = MinorDegreeRequirements.objects.get(minor=minor)
            #add intro to english, math, science, and social science
            minor_requirements.courses.add(Course.objects.get(course_name=f'Intro to English'))
            minor_requirements.courses.add(Course.objects.get(course_name=f'Intro to Math'))
            minor_requirements.courses.add(Course.objects.get(course_name=f'Intro to Science'))
            minor_requirements.courses.add(Course.objects.get(course_name=f'Intro to History'))
            #add concepts of english, math, science, and social science
            minor_requirements.courses.add(Course.objects.get(course_name=f'Concepts of English'))
            minor_requirements.courses.add(Course.objects.get(course_name=f'Concepts of Math'))
            minor_requirements.courses.add(Course.objects.get(course_name=f'Concepts of Science'))
            minor_requirements.courses.add(Course.objects.get(course_name=f'Concepts of History'))
            minor_requirements.save()
