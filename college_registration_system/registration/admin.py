from django.contrib import admin
from .models import (
    User, Login, Admin, Student, Undergraduate, Undergrad_Full_Time, Undergrad_Part_Time,
    Graduate, Grad_Full_Time, Grad_Part_Time, Faculty, Faculty_FullTime, Faculty_PartTime,
    StatisticsOffice, Department, Building, Room, Lab, Lecture, Semester, CourseSection,
    Course, CoursePrereq, Enrollment, StudentHistory, FacultyHistory, Attendance, Hold,
    Timeslot, Day, Period, Major, Minor, MajorDegreeRequirements, MinorDegreeRequirements
)

from django.contrib.auth.hashers import make_password

class LoginAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.password = make_password(obj.password)  # Hash the password only if it has changed
        super().save_model(request, obj, form, change)

class RoomAdmin(admin.ModelAdmin):
    list_display = ('formatted_room_no',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.order_by('building__bldg_name', 'room_no')

    def formatted_room_no(self, obj):
        return f"{obj.building.bldg_name} {str(obj.room_no).rjust(3, '0')}"
    formatted_room_no.admin_order_field = 'room_no'  # Allows column order sorting
    formatted_room_no.short_description = 'Room No'
def add_specific_course_to_requirements(modeladmin, request, queryset):
    # Specify the course to add (e.g., by its ID)
    specified_course_name = "Intro to Fitness"  # Replace with the actual course ID

    # Fetch the course object
    specified_course = Course.objects.get(course_name=specified_course_name)

    # Iterate over the queryset and add the course if not present
    for requirement in queryset:
        if not requirement.courses.filter(course_name=specified_course_name).exists():
            requirement.courses.add(specified_course)

add_specific_course_to_requirements.short_description = "Add specified course to selected requirements"

class MajorDegreeRequirementsAdmin(admin.ModelAdmin):
    filter_horizontal = ('courses',)
    search_fields = ['courses__course_name']
    actions = [add_specific_course_to_requirements]

class MinorDegreeRequirementsAdmin(admin.ModelAdmin):
    filter_horizontal = ('courses',)
    search_fields = ['courses__course_name']
    actions = [add_specific_course_to_requirements]

class UserAdmin(admin.ModelAdmin):
    #search by name
    search_fields = ['first_name', 'last_name', 'user_type']
    #display list of users

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.order_by('user_type','last_name', 'first_name')

class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ('course', 'crn', 'semester', 'faculty', 'room', 'timeslot')
    list_filter = ('semester', 'faculty', 'room', 'timeslot')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.order_by('course', 'crn')

    def course(self, obj):
        return obj.course_id
    course.admin_order_field = 'course_id'  # Allows column order sorting

    def crn(self, obj):
        return obj.crn
    crn.admin_order_field = 'crn'  # Allows column order sorting

    def faculty(self, obj):
        return obj.faculty_id
    faculty.admin_order_field = 'faculty_id'  # Allows column order sorting

    def room(self, obj):
        return obj.room_id
    room.admin_order_field = 'room_id'  # Allows column order sorting

    def timeslot(self, obj):
        return obj.timeslot_id
    timeslot.admin_order_field = 'timeslot_id'  # Allows column order sorting

admin.site.register(Login, LoginAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Admin)
admin.site.register(Student)
admin.site.register(Undergraduate)
admin.site.register(Undergrad_Full_Time)
admin.site.register(Undergrad_Part_Time)
admin.site.register(Graduate)
admin.site.register(Grad_Full_Time)
admin.site.register(Grad_Part_Time)
admin.site.register(Faculty)
admin.site.register(Faculty_FullTime)
admin.site.register(Faculty_PartTime)
admin.site.register(StatisticsOffice)
# admin.site.register(TermList)
admin.site.register(Department)
admin.site.register(Building)
admin.site.register(Room, RoomAdmin)
admin.site.register(Lab)
admin.site.register(Lecture)
admin.site.register(Semester)
admin.site.register(CourseSection, CourseSectionAdmin)
admin.site.register(Course)
admin.site.register(CoursePrereq)
admin.site.register(Enrollment)
admin.site.register(StudentHistory)
admin.site.register(FacultyHistory)
admin.site.register(Attendance)
admin.site.register(Hold)
admin.site.register(Timeslot)
admin.site.register(Major)
admin.site.register(Minor)
admin.site.register(MajorDegreeRequirements, MajorDegreeRequirementsAdmin)
admin.site.register(MinorDegreeRequirements, MinorDegreeRequirementsAdmin)
# admin.site.register(TimeSlotDay)
# admin.site.register(TimeSlotPeriod)
admin.site.register(Day)
admin.site.register(Period)
