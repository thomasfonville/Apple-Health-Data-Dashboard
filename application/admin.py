from django.contrib import admin

# Register your models here.
from .models import RunningWorkoutData
from .models import HeartRateData
from .models import WorkoutRoute 
from .models import StepCountData

admin.site.register(RunningWorkoutData)
admin.site.register(HeartRateData)
admin.site.register(WorkoutRoute)
admin.site.register(StepCountData)