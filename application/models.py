from django.db import models
from xml.etree import ElementTree as ET
from django.contrib.auth.models import User


# Workout model database

class RunningWorkoutData(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    duration = models.DecimalField(max_digits=10, decimal_places=2)  # Changed from CharField
    source = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    distance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    cals_burned = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    class Meta:
        ordering = ['-start_date']
    
    @property
    def cadence(self):
        steps_per_minute = [data.steps_per_minute for data in self.step_count_data.all()]
        return sum(steps_per_minute) / len(steps_per_minute) if steps_per_minute else 0
        

class HeartRateData(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    workout = models.ForeignKey(RunningWorkoutData, on_delete=models.CASCADE, related_name='heart_rate_data', null=True)
    heart_rate = models.FloatField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()


class StepCountData(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    workout = models.ForeignKey(RunningWorkoutData, on_delete=models.CASCADE, related_name='step_count_data', null=True)
    step_count = models.IntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    @property
    def steps_per_minute(self):
        duration_in_minutes = (self.end_date - self.start_date).total_seconds() / 60
        return self.step_count / duration_in_minutes if duration_in_minutes else 0
    

class WorkoutRoute(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    workout = models.ForeignKey(RunningWorkoutData, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=9, decimal_places=6) # range -90 to +90 (degrees)
    longitude = models.DecimalField(max_digits=9, decimal_places=6) # range -180 to +180 (degrees)
    elevation = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True) # null and blank set to True to allow for missing elevation data

    class Meta:
        verbose_name = "Workout Route"
        verbose_name_plural = "Workout Routes"

    def __str__(self):
        return f"Workout {self.workout.id} - Lat: {self.latitude}, Lon: {self.longitude}, Ele: {self.elevation}"







 