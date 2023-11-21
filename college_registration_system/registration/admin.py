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


admin.site.register(Login, LoginAdmin)
admin.site.register(User)
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
admin.site.register(CourseSection)
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
admin.site.register(MajorDegreeRequirements)
admin.site.register(MinorDegreeRequirements)
# admin.site.register(TimeSlotDay)
# admin.site.register(TimeSlotPeriod)
admin.site.register(Day)
admin.site.register(Period)
