import random
import uuid
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from faker import Faker
from django.db.models import Count
from registration.models import Attendance, Building, Department, Room, Semester,CoursePrereq, StudentHistory, Timeslot, User, Student, Faculty, Course, CourseSection, Enrollment, Major, Faculty_FullTime, Faculty_PartTime, Grad_Part_Time, Grad_Full_Time, Undergrad_Part_Time, Undergrad_Full_Time, Graduate, Undergraduate,Major,Minor,MajorDegreeRequirements,MinorDegreeRequirements
import datetime as dt
from collections import defaultdict
class Command(BaseCommand):
    help = 'Populates the database with random data'

    majors_by_department = {
        'Math': ['Math', 'Statistics'],
        'Science': ['Science', 'Environmental Science'],
        'Arts': ['Arts', 'Fine Arts'],
        'English': ['English', 'Creative Writing'],
        'History': ['History', 'Historical Studies'],
        'Computer Science': ['Computer Science', 'Machine Learning'],
        'Business': ['Business', 'Finance'],
        'Engineering': ['Engineering', 'Mechanical Engineering'],
        'Music': ['Music', 'Music Theory'],
        'Theater': ['Theater', 'Dramatic Arts'],
        'Dance': ['Dance', 'Choreography'],
        'Biology': ['Biology', 'Molecular Biology'],
        'Chemistry': ['Chemistry', 'Biochemistry'],
        'Physics': ['Physics', 'Astrophysics'],
        'Geology': ['Geology', 'Earth Sciences'],
        'Psychology': ['Psychology', 'Clinical Psychology'],
        'Sociology': ['Sociology', 'Social Theory'],
        'Anthropology': ['Anthropology', 'Cultural Anthropology'],
        'Philosophy': ['Philosophy', 'Ethics'],
        'Religion': ['Religion', 'Theological Studies'],
        'Economics': ['Economics', 'International Economics'],
        'Political Science': ['Political Science', 'International Relations'],
        'Foreign Language': ['Foreign Language', 'Linguistics'],
        'Education': ['Education', 'Curriculum and Instruction'],
        'Nursing': ['Nursing', 'Healthcare Administration'],
        'Medicine': ['Medicine', 'Biomedical Sciences'],
        'Law': ['Law', 'Criminal Law'],
        'Criminal Justice': ['Criminal Justice', 'Forensic Science'],
        'Architecture': ['Architecture', 'Urban Design'],
        'Agriculture': ['Agriculture', 'Agronomy'],
        'Veterinary Medicine': ['Veterinary Medicine', 'Animal Science'],
        'Dentistry': ['Dentistry', 'Orthodontics'],
        'Pharmacy': ['Pharmacy', 'Pharmacology'],
        'Library Science': ['Library Science', 'Information Management'],
        'Journalism': ['Journalism', 'Media Studies'],
        'Communications': ['Communications', 'Digital Communication'],
        'Public Relations': ['Public Relations', 'Corporate Communication'],
        'Social Work': ['Social Work', 'Community Health'],
        'Public Administration': ['Public Administration', 'Governmental Affairs'],
        'Urban Planning': ['Urban Planning', 'Community Development'],
        'Hospitality': ['Hospitality', 'Tourism Management'],
        'Recreation': ['Recreation', 'Sports Management'],
        'Fitness': ['Fitness', 'Kinesiology'],
        'Cosmetology': ['Cosmetology', 'Beauty Therapy'],
        'Culinary Arts': ['Culinary Arts', 'Food Science']
    }
    def handle(self, *args, **kwargs):
        self.stdout.write("Select an option to proceed:")
        self.stdout.write("1: Generate all data")
        self.stdout.write("2: Generate rooms")
        self.stdout.write("3: Generate users")
        self.stdout.write("4: Generate courses")
        self.stdout.write("5: Generate pre-requisites")
        self.stdout.write("6: Generate sections")
        self.stdout.write("7: Generate enrollments")
        self.stdout.write("8: Remove underfilled sections")
        self.stdout.write("9: Generate major and minor requirements")
        self.stdout.write("10: Generate attendances")
        self.stdout.write("0: Delete all data except users: Super Admin, William Krasnov, and R Khusro, and departments")
        self.stdout.write("Z: Discrepencies Check")
        choice = input("Enter your choice (0-10,Z): ")

        fake = Faker()

        if choice == '1':
            self.create_rooms(fake)
            # self.create_majors_minors(fake)
            self.create_users(fake)
            # self.create_courses(fake)
            self.create_sections(fake)
            # self.create_major_minor_requirements(fake)
            # self.create_course_prereqs(fake)
            self.enroll_students(fake)
            self.remove_underfilled_sections(fake)
            self.generate_attendances(fake)
        elif choice == '2':
            self.create_rooms(fake)
        elif choice == '3':
            self.create_users(fake)
        elif choice == '4':
            self.create_courses(fake)
        elif choice == '5':
            self.create_course_prereqs(fake)
        elif choice == '6':
            self.create_sections(fake)
        elif choice == '7':
            self.enroll_students(fake)
        elif choice == '8':
            self.remove_underfilled_sections(fake)
        elif choice == '9':
            self.create_major_minor_requirements(fake)
        elif choice == '10':
            self.generate_attendances(fake)
        elif choice == '0':
            self.delete_all_data(fake)
        elif choice == 'Z':
            self.check_enrollment_conflits(fake)
        else:
            self.stdout.write("Invalid choice.")

    def create_majors_minors(self, fake):
        for department in Department.objects.all():
            if department.department_name == 'Undecided':
                continue
            if department.department_name == 'Other':
                continue
            for major_name in self.majors_by_department[department.department_name]:
                major, created = Major.objects.get_or_create(
                    department=department,
                    major_name=major_name,
                )
                if created:
                    print(f'Created major {major}')
                else:
                    print(f'Major {major} already exists')

                # Create minor
                minor, created = Minor.objects.get_or_create(
                    department=department,
                    minor_name=major_name,
                )
                if created:
                    print(f'Created minor {minor}')
                else:
                    print(f'Minor {minor} already exists')


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
        for _ in range(1000):

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
            # s.student_type=random.choice(['Undergraduate', 'Graduate'])
            if fake.random_int(min=0,max=4) == 0:
                s.student_type='Graduate'
            else:
                s.student_type='Undergraduate'
            s.major_id=Major.objects.order_by('?').first()
            s.enrollment_year=fake.random_int(min=2015, max=2020)
            # s.studentID=fake.unique.random_int(min=7000005, max=7999999)
            s.save()
            print(f'Created student {user.first_name} {user.last_name} with id {s.studentID}')

        for _ in range(150):
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
            )[0]
            f.fac_type=random.choice(['FullTime', 'PartTime'])
            f.specialty=fake.job()
            f.rank=random.choice(['Professor', 'Assistant Professor', 'Adjunct Professor', 'Teaching Assistant'])
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
                    course = Course.objects.create(
                            course_name=f'{course_prefix} {major.major_name}',
                            department=major.department,
                            course_type=course_level,
                            course_number=fake.random_int(min=100 if course_level == 'UnderGrad' else 500, max=499 if course_level == 'UnderGrad' else 899),
                            no_of_credits=random.choice([3, 4]),
                            description=f'This is a(n) {course_level} course in {major.major_name}',
                    )
                    print(f'Created course {course.course_name}')
            except IntegrityError:
                print(f'Course already exists')
        # create prereqs for concepts of courses and advanced subjects of courses

    def create_course_prereqs(self, fake):
        for course in Course.objects.all():
            if course.course_name.startswith('Concepts of') or course.course_name.startswith('Advanced Subjects of'):
                #set prereq to be lower level course in same major
                if course.course_name.startswith('Concepts of'):
                    print(f'Creating prereq for {course.course_name}')
                    prereq = Course.objects.filter(course_name__startswith='Intro to'+course.course_name.removeprefix('Concepts of'),department=course.department).first()
                    CoursePrereq.objects.create(
                        course=course,
                        pr_course=prereq,
                        min_grade='C',
                        date_of_last_update=dt.date.today()
                    )
                elif course.course_name.startswith('Advanced Subjects of'):
                    print(f'Creating prereq for {course.course_name}')
                    prereq = Course.objects.filter(course_name__startswith='Concepts of'+course.course_name.removeprefix('Advanced Subjects of'),department=course.department).first()
                    CoursePrereq.objects.create(
                        course=course,
                        pr_course=prereq,
                        min_grade='C',
                        date_of_last_update=dt.date.today()
                    )
                # course.description += prereq.course_name + '\n'
                course.save()

    def create_sections(self, fake):
        for semester in Semester.objects.all().order_by('start_date'):
            # if semester.semester_name == 'Fall 2023':
            #     continue
            faculty_course_count = defaultdict(int)
            for course in Course.objects.all().order_by('?'):
                # Create 1-2 sections for each course
                num_of_sections = random.randint(1, 2)
                if course.course_name.startswith('Advanced Subjects of'):
                    num_of_sections = random.randint(0, 1)
                print(f'Creating {num_of_sections} sections for {course.course_name} for {semester}')

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

                        #if fall 2023 then skip
                        # if semester.semester_name == 'Fall 2023':
                        #     continue
                    print(f'Creating section for {course.course_name} taught by {selected_faculty}')
                    if course.course_name.startswith('Intro to'):
                        CourseSection.objects.create(
                            course=course,
                            available_seats=fake.random_int(min=50, max=200),
                            faculty=selected_faculty,
                            semester=semester,
                            timeslot=fake.random_element(elements=Timeslot.objects.all()),
                            room=fake.random_element(elements=Room.objects.all()),
                        )
                    else:
                        CourseSection.objects.create(
                            course=course,
                            available_seats=fake.random_int(min=25, max=50),
                            faculty=selected_faculty,
                            semester=semester,
                            timeslot=fake.random_element(elements=Timeslot.objects.all()),
                            room=fake.random_element(elements=Room.objects.all()),
                        )
                    # Update the faculty's course count
                    faculty_course_count[selected_faculty.user.id] += 1

    def remove_underfilled_sections(self, fake):
        for section in CourseSection.objects.all():
            # if section.student_history_set.count() < 5:
            #if amount of student_history objects is less than 5 for section, delete the section
            if section.studenthistory_set.count() < 5:
                if section.semester.semester_name=='Spring 2024':
                    continue
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
            #add other intro courses from same department
            for course in Course.objects.filter(course_name__startswith='Intro to',department=major.department):
                #if course is not already in major requirements, add it
                if not major_requirements.courses.filter(course_name=course.course_name).exists():
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
            for course in Course.objects.filter(course_name__startswith='Intro to',department=major.department):
                #if course is not already in major requirements, add it
                if not minor_requirements.courses.filter(course_name=course.course_name).exists():
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

    def enroll_students(self,fake):
        def get_major_priority_ids(student):
            # Return a list of course IDs prioritized for the student's major
            return list(Course.objects.filter(course_name__contains=student.major_id.major_name)
                                        .values_list('course_id', flat=True))

        def get_major_course_ids(student):
            # Return a list of course IDs required for the student's major
            return list(MajorDegreeRequirements.objects.filter(major=student.major_id)
                                                    .values_list('courses__course_id', flat=True))

        def get_department_course_ids(student):
            # Return a list of course IDs offered by the student's department
            return list(Course.objects.filter(department=student.major_id.department)
                                    .values_list('course_id', flat=True))

        def get_other_course_ids(student):
            # Return a list of other course IDs
            return list(Course.objects.exclude(course_id__in=get_major_course_ids(student))
                                    .values_list('course_id', flat=True))

        def get_available_courses(course_ids, semester, student):
            # Get sets of course IDs that the student has completed with a grade of 'C' or higher
            completed_course_ids = set(StudentHistory.objects.filter(
                student=student,
                grade__in=['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C']
            ).values_list('section__course__course_id', flat=True))

            # Get sets of course IDs where the student is currently enrolled in the given semester
            current_enrollment_ids = set(StudentHistory.objects.filter(
                student=student,
                section__semester=semester,
                grade='NA'
            ).values_list('section__course__course_id', flat=True))

            # Get sets of course IDs where the student has not met the prerequisites
            unmet_prereqs_ids = set(CoursePrereq.objects.exclude(
                pr_course__course_id__in=completed_course_ids
            ).values_list('course__course_id', flat=True))

            # Get sets of course IDs where in that semester, the student already has a course with the same period on the same day
            # conflicting_course_ids = set(StudentHistory.objects.filter(
            #     student=student,
            #     section__semester=semester,
            #     section__timeslot__period__in=[section.timeslot.period for section in StudentHistory.objects.filter(student=student, section__semester=semester)]
            # ).values_list('section__course__course_id', flat=True))

            # Combine the sets and exclude these courses
            excluded_course_ids = unmet_prereqs_ids.union(completed_course_ids).union(current_enrollment_ids)

            # Filter courses based on the given course IDs and excluding courses with unmet prerequisites or already completed/currently enrolled courses
            courses_qs = Course.objects.filter(course_id__in=course_ids).exclude(course_id__in=excluded_course_ids)
            return courses_qs

        def prioritize_sections(available_courses, semester):
            # Return a list of sections, prioritized by those with the lowest enrollment first
            sections = []
            for course in available_courses:
                sections.extend(list(CourseSection.objects.filter(course=course, semester=semester)
                                    .annotate(num_enrolled=Count('enrollment'))
                                    .order_by('num_enrolled')))
            return sections
        def enroll_student_in_section(student, section, semester):
            # Check if the student is already enrolled in the same course for the same semester
            if not StudentHistory.objects.filter(student=student, section__course=section.course, semester=semester).exists():
                grade = 'NA' if semester.semester_name == 'Spring 2024' else random.choice(['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'F'])
                if semester.semester_name == 'Spring 2024':
                    Enrollment.objects.create(
                        student=student,
                        section=section,
                        grade=grade,
                        date_of_enrollment=dt.date.today()
                    )
                else:
                    StudentHistory.objects.create(
                        student=student,
                        section=section,
                        semester=semester,
                        grade=grade,
                    )
                section.available_seats -= 1
                section.save()



        #make sure Fall 2022 followed by Spring 2023 followed by Fall 2023 followed by Spring 2024
        # all_semesters = Semester.objects.get(semester_name='Fall 2022') | Semester.objects.get(semester_name='Spring 2023') | Semester.objects.get(semester_name='Fall 2023') |
        semester = Semester.objects.get(semester_name='Spring 2024')

        # for semester in all_semesters:
        for student in Student.objects.all().order_by('?'):
            # start_semester = random.choice(all_semesters)
            # if semester.start_date < start_semester.start_date:
            #     continue

            if student.student_type=="Undergraduate":
                undergrad = Undergraduate.objects.get(student=student)
                if undergrad.undergrad_student_type == 'PartTime':
                    course_limit = 2
                else:
                    course_limit = 4
            else:
                grad = Graduate.objects.get(student=student)
                if grad.grad_student_type == 'PartTime':
                    course_limit = 2
                else:
                    course_limit = 4
            # course_limit = 2 if student.student_type == 'PartTime' else 4
            enrolled_courses = Enrollment.objects.filter(student=student).count()



            for course_ids in [get_major_priority_ids(student), get_major_course_ids(student), get_department_course_ids(student), get_other_course_ids(student)]:
                available_courses = get_available_courses(course_ids, semester, student)
                sections_to_enroll = prioritize_sections(available_courses, semester)

                for section in sections_to_enroll:
                    # If student is already enrolled in the course for this semester, skip this section
                    if StudentHistory.objects.filter(student=student, section__course=section.course, semester=semester).exists():
                        continue

                    if enrolled_courses >= course_limit:
                        break

                    if section.available_seats > 0:
                        enroll_student_in_section(student, section, semester)
                        print(f'Enrolled {student} in {section} for {semester}')
                        enrolled_courses += 1

                        # Update the available courses and sections after successful enrollment
                        if enrolled_courses < course_limit:
                            available_courses = get_available_courses(course_ids, semester, student)
                            sections_to_enroll = prioritize_sections(available_courses, semester)


    def generate_attendances(self, fake):
        for history in StudentHistory.objects.all():
            print(f'Generating attendances for {history.student} in {history.section}')
            if history.semester.semester_name != 'Spring 2024':
                # Iterate through each class day in the semester
                start_date = history.semester.start_date
                end_date = history.semester.end_date
                current_date = start_date

                while current_date <= end_date:
                    print(f'\tGenerating attendance: {current_date}')
                    # Check if current date is a valid class day
                    class_days = [day.weekday for day in history.section.timeslot.days.all()]
                    if current_date.strftime('%A') in class_days:
                        # 1/5 chance of being absent
                        present = random.choice([True, True, True, True, False])
                        Attendance.objects.create(
                            student=history.student,
                            section=history.section,
                            date_of_class=current_date,
                            present=present
                        )

                    # Move to the next day
                    current_date += dt.timedelta(days=1)
    def assign_department_staff(self, fake):
        for dept in Department.objects.all():
            all_faculty = Faculty.objects.all()
            valid_faculty = []
            for faculty in all_faculty:
                if faculty.departments.filter(department_name=dept.department_name).exists():
                    valid_faculty.append(faculty)

            dept.chair_id = random.choice(valid_faculty)
            print(f"Chair of {dept.department_name} is {dept.chair_id}")
            dept.manager_id = random.choice(valid_faculty)
            print(f"Manager of {dept.department_name} is {dept.manager_id}")
            dept.save()

    def check_enrollment_conflits(self, fake):
        #print how many students are fulltime and only enrolled in 2 courses
        countFTNotEnrolledIn2 = 0
        for student in Student.objects.all():

            is_FT = False
            grad=None
            undergrad=None
            if student.student_type=="Undergraduate":
                undergrad = Undergraduate.objects.get(student=student)
                if undergrad.undergrad_student_type == 'PartTime':
                    is_FT = False
                else:
                    is_FT = True
            else:
                grad = Graduate.objects.get(student=student)
                if grad.grad_student_type == 'PartTime':
                    is_FT = False
                else:
                    is_FT = True
            if is_FT:
                if Enrollment.objects.filter(student=student).count() <= 2:
                    countFTNotEnrolledIn2 += 1
            else:
                pass
        print(f"{countFTNotEnrolledIn2} students are fulltime and only enrolled in 2 courses")
        #if any student is enrolled in two sections of the same course in the same semester, delete one of the enrollments
        for student in Student.objects.all():
            is_FT = False
            grad=None
            undergrad=None
            if student.student_type=="Undergraduate":
                undergrad = Undergraduate.objects.get(student=student)
                if undergrad.undergrad_student_type == 'PartTime':
                    is_FT = False
                else:
                    is_FT = True
            else:
                grad = Graduate.objects.get(student=student)
                if grad.grad_student_type == 'PartTime':
                    is_FT = False
                else:
                    is_FT = True
            for enroll in Enrollment.objects.filter(student=student):
                section = enroll.section
                if Enrollment.objects.filter(student=student, section=section).count() > 1:
                    print(f"Student {student} is enrolled in {section} more than once. Deleting one of the enrollments...")
                    Enrollment.objects.filter(student=student, section=section).first().delete()
                #if student is enrolled in two sections of the same day and time, delete one of the enrollments
                for other_enroll in Enrollment.objects.filter(student=student):
                    other_section = other_enroll.section
                    if section != other_section:
                        if section.timeslot == other_section.timeslot:
                            if Enrollment.objects.filter(student=student, section=section).exists() and Enrollment.objects.filter(student=student, section=other_section).exists():
                                print(f"Student {student} is enrolled in {section} and {other_section} at the same time. Deleting one of the enrollments...")
                                Enrollment.objects.filter(student=student, section=section).first().delete()
                if Enrollment.objects.filter(student=student).count() <= 2:
                    if grad is not None:
                        grad.grad_student_type = 'PartTime'
                        grad.save()
                    else:
                        undergrad.undergrad_student_type = 'PartTime'
                        undergrad.save()



            if not is_FT:
                #if student is part time yet enrolled in more than 2 courses, delete enrollments until only 2 remain
                if Enrollment.objects.filter(student=student).count() > 2:
                    print(f"Student {student} is enrolled in more than 2 courses. Deleting enrollments until only 2 remain...")
                    while Enrollment.objects.filter(student=student).count() > 2:
                        Enrollment.objects.filter(student=student).first().delete()


    def delete_all_data(self, fake):
        #delete all data except users: Super Admin, William Krasnov, and R Khusro, and departments
        print("Deleting all users except: Super Admin, William Krasnov, and R Khusro, and departments...")
        User.objects.exclude(first_name='Super').exclude(last_name='Krasnov').exclude(first_name='R').exclude(first_name='Statistics').exclude(first_name='Stats').delete()
        print("Deleting all rooms...")
        Room.objects.all().delete()
        # print("Deleting all courses...")
        # Course.objects.all().delete()
        print("Deleting all sections...")
        CourseSection.objects.all().delete()
        print("Deleting all enrollments...")
        Enrollment.objects.all().delete()
        # print("Deleting all Majors and Minors...")
        # # Major.objects.all().delete()
        # Minor.objects.all().delete()
        # print("Deleting all Major and Minor Requirements...")
        # MajorDegreeRequirements.objects.all().delete()
        # MinorDegreeRequirements.objects.all().delete()
        # print("Deleting all Course Prereqs...")
        # CoursePrereq.objects.all().delete()
        print("deleting all faculty and student data...")
        Faculty_FullTime.objects.all().delete()
        Faculty_PartTime.objects.all().delete()
        Grad_Part_Time.objects.all().delete()
        Grad_Full_Time.objects.all().delete()
        Undergrad_Part_Time.objects.all().delete()
        Undergrad_Full_Time.objects.all().delete()
        Graduate.objects.all().delete()
        Undergraduate.objects.all().delete()
        Student.objects.all().delete()
        Faculty.objects.all().delete()
        print("Deleted all data except users: Super Admin, William Krasnov, and R Khusro, and departments, and building(s)")