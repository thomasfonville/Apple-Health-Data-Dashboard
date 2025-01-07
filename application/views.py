from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User 
from xml.etree import ElementTree as ET
from .models import RunningWorkoutData, HeartRateData, StepCountData, WorkoutRoute
from .forms import UploadFileForm, WorkoutFilterForm, NewUserForm, LoginForm
from django.db.models import Q, Avg, Func, IntegerField, DecimalField, Sum, FloatField, F, ExpressionWrapper, fields, Max
from datetime import datetime, timedelta
from django.db.models.functions import ExtractMonth, ExtractYear, Round, Coalesce, ExtractHour
from django.utils import timezone
import math, os, zipfile, shutil, json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from collections import Counter
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from collections import Counter
from dateutil.parser import parse
import json
import time




class Round(Func):
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 0)'
    output_field = DecimalField()


def home(request):
    return render(request, 'home.html')


def round_half_up(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n*multiplier + 0.5) / multiplier


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm()
    return render (request=request, template_name='register.html', context={"register_form":form})


def login_request(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid form input.")
    else:
        form = LoginForm()
    return render(request=request, template_name='login.html', context={"login_form":form})


def logout_request(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')

def get_heart_rate_zones(max_heart_rate):
    return {
        'Zone 1': (50, 60),
        'Zone 2': (60, 70),
        'Zone 3': (70, 80),
        'Zone 4': (80, 90),
        'Zone 5': (90, 100),
    }

def dashboard(request):
    if request.user.is_authenticated:
        user_obj = request.user
    else:
        # If not logged in, use the demo account
        user_obj = User.objects.get(username='demo')

    # Now reference user_obj in place of request.user in all queries:
    user_running_workouts = RunningWorkoutData.objects.filter(user=user_obj)
    has_data = user_running_workouts.exists()
    distance_labels, distances, hr_labels, heart_rates = [], [], [], []
    pace_labels, paces_decimal, cadence_labels, cadences = [], [], [], []
    average_cadence, total_distance, average_hr = 0, 0, 0
    fastest_hour_display, worst_hour_display = "N/A", 'N/A'
    heart_rate_range_zone_2, percentage_in_zone_2 = "N/A", "N/A"
    zone_times_per_workout, run_dates = "N/A", "N/A"
    routes_per_workout = []
    average_pace = "N/A" 

    if has_data:
        distance_data = user_running_workouts.annotate(
            month=ExtractMonth('start_date'),
            year=ExtractYear('start_date')
        ).values('month', 'year').annotate(distance_sum=Sum('distance')).order_by('year', 'month')
        distance_labels = ['{}/{}'.format(d['month'], d['year']) for d in distance_data]
        distances = [float(d['distance_sum']) for d in distance_data]

        heart_rate_data = user_running_workouts.exclude(heart_rate_data__heart_rate__isnull=True).annotate(
            avg_hr=Round(Avg('heart_rate_data__heart_rate'), output_field=IntegerField())
        ).order_by('start_date')
        hr_labels = [hr.start_date.strftime('%Y-%m-%d') for hr in heart_rate_data]
        heart_rates = [hr.avg_hr for hr in heart_rate_data if hr.avg_hr is not None]

        total_duration_seconds = sum(workout.duration for workout in user_running_workouts)
        total_distance_miles = sum(workout.distance for workout in user_running_workouts)

        if total_distance_miles > 0:
            # Calculate average pace in seconds per mile
            average_pace_seconds_per_mile = total_duration_seconds / total_distance_miles
            # Convert average pace to minutes:seconds format
            average_pace_minutes = int(average_pace_seconds_per_mile // 60)
            average_pace_seconds = int(average_pace_seconds_per_mile % 60)
            average_pace = f"{average_pace_minutes}:{average_pace_seconds:02d}"
        else:
            average_pace = "N/A"

        # Calculate pace in decimal minutes per mile
        pace_data = user_running_workouts.annotate(
            pace_seconds_per_mile=ExpressionWrapper(F('duration') / F('distance'), output_field=FloatField())
        ).order_by('start_date')

        pace_labels = [workout.start_date.strftime('%Y-%m-%d') for workout in pace_data]
        paces_decimal = [(pace.pace_seconds_per_mile / 60) for pace in pace_data]  # Convert seconds to decimal minutes

        workout_data = user_running_workouts.order_by('start_date').prefetch_related('step_count_data')
        cadence_labels = [w.start_date.strftime('%Y-%m-%d') for w in workout_data]
        cadences = [round(w.cadence) for w in workout_data]

        average_cadence = sum([w.cadence for w in workout_data]) / len(workout_data) if workout_data else 0
        average_cadence = int(average_cadence)

        total_distance = user_running_workouts.aggregate(
            total_distance=Coalesce(Sum('distance'), 0, output_field=DecimalField())
        )['total_distance']
        total_distance = round(total_distance, 2)

        average_hr = user_running_workouts.aggregate(
            avg_hr=Coalesce(Avg('heart_rate_data__heart_rate'), 0, output_field=FloatField())
        )['avg_hr']
        average_hr = round(average_hr) if average_hr is not None else 0

        # Correctly annotate the workout data with pace
        workouts_with_pace = user_running_workouts.annotate(
            hour=ExtractHour('start_date'),  # Extracts the hour part of the start_date
            pace=ExpressionWrapper(F('duration') / F('distance'), output_field=FloatField())  # Calculates pace
        )

        # Calculate average pace for each hour and find the fastest
        fastest_hour_data = workouts_with_pace.values('hour').annotate(avg_pace=Avg('pace')).order_by('avg_pace').first()

        # Calculate average pace for each hour and find the slowest
        worst_hour_data = workouts_with_pace.values('hour').annotate(avg_pace=Avg('pace')).order_by('-avg_pace').first()

        if fastest_hour_data:
            hour = fastest_hour_data['hour']  # This will be in UTC
            # Adjust for your time zone here if necessary
            hour_adjusted = (hour - 5) % 24  # Simplistic adjustment for EST without considering DST
            suffix = "AM" if hour_adjusted < 12 else "PM"
            hour_formatted = hour_adjusted % 12 or 12
            fastest_hour_display = f"{hour_formatted} {suffix}"

        if worst_hour_data:
            hour = worst_hour_data['hour']  # This will be in UTC
            # Adjust for your time zone here if necessary
            hour_adjusted = (hour - 5) % 24  # Simplistic adjustment for EST without considering DST
            suffix = "AM" if hour_adjusted < 12 else "PM"
            hour_formatted = hour_adjusted % 12 or 12
            worst_hour_display = f"{hour_formatted} {suffix}"

      # Retrieve the maximum heart rate from the user's heart rate data
        max_heart_rate_query = HeartRateData.objects.filter(
            user=user_obj,
            workout__isnull=False
        ).aggregate(max_heart_rate=Max('heart_rate'))

        max_heart_rate = max_heart_rate_query.get('max_heart_rate')

        # Proceed only if a maximum heart rate has been successfully retrieved
        if max_heart_rate:
            # Generate heart rate zones based on the maximum heart rate
            heart_rate_zones = get_heart_rate_zones(max_heart_rate)
            
            # Initialize variables for tracking zone times and other statistics
            zone_times_per_workout = {zone: [0] * user_running_workouts.count() for zone in heart_rate_zones}
            run_dates = []
            total_time_seconds = 0.0
            workout_index = 0
            time_in_zone_2_seconds = 0.0

            # Calculate heart rate zone ranges and display for Zone 2
            zone_2_range = heart_rate_zones['Zone 2']
            zone_2_lower_limit = int((zone_2_range[0] / 100) * max_heart_rate)
            zone_2_upper_limit = int((zone_2_range[1] / 100) * max_heart_rate)
            heart_rate_range_zone_2 = f"{zone_2_lower_limit}-{zone_2_upper_limit} bpm"

            # Iterate through each workout to calculate time spent in each heart rate zone
            for workout in user_running_workouts:
                run_dates.append(workout.start_date.strftime('%Y-%m-%d'))
                workout_duration_seconds = float(workout.duration) * 60
                total_time_seconds += workout_duration_seconds

                for zone, (lower_pct, upper_pct) in heart_rate_zones.items():
                    lower_limit = int((lower_pct / 100) * max_heart_rate)
                    upper_limit = int((upper_pct / 100) * max_heart_rate)

                    # Fetch heart rate data within the zone and calculate time spent
                    hr_data_in_zone = workout.heart_rate_data.filter(
                        heart_rate__gte=lower_limit,
                        heart_rate__lte=upper_limit,
                        start_date__gte=workout.start_date,
                        end_date__lte=workout.end_date
                    )
                    
                    workout_time_in_zone_seconds = sum([
                        (data.end_date - data.start_date).total_seconds() for data in hr_data_in_zone
                    ])

                    # Accumulate time in the current zone, converting seconds to minutes
                    zone_times_per_workout[zone][workout_index] += workout_time_in_zone_seconds / 60.0

                    if zone == 'Zone 2':
                        time_in_zone_2_seconds += workout_time_in_zone_seconds

                workout_index += 1

            # Adjusted calculation for the percentage of time spent in Zone 2
            # Ensure total workout time is calculated in minutes for consistency with zone time calculations
            total_workout_minutes = total_time_seconds / 60  # Convert total workout time from seconds to minutes

            if total_workout_minutes > 0:
                percentage_in_zone_2 = (time_in_zone_2_seconds / total_workout_minutes) * 100
            else:
                percentage_in_zone_2 = 0

            percentage_in_zone_2 = round(percentage_in_zone_2, 2)  # Round the result to 2 decimal places
        else:
            heart_rate_range_zone_2 = "N/A"  # Assign "N/A" if the max heart rate can't be determined


        workout_ids = WorkoutRoute.objects.filter(user=user_obj).values_list('workout', flat=True).distinct()
        workouts = user_running_workouts.filter(id__in=workout_ids)

        route_workout_ids = WorkoutRoute.objects.filter(user=user_obj).values_list('workout__id', flat=True)
        route_counter = Counter(route_workout_ids)

        if route_counter:
            max_freq = max(route_counter.values())
            route_counter = {workout_id: freq / max_freq for workout_id, freq in route_counter.items()}

        routes_per_workout = []

        for workout in workouts:
            workout_routes = [{
                'latitude': float(route.latitude),
                'longitude': float(route.longitude),
                'frequency': route_counter.get(workout.id, 0)
            } for route in WorkoutRoute.objects.filter(workout=workout)]

            if workout_routes:
                routes_per_workout.append(workout_routes)

    return render(request, 'dashboard.html', {
        'distance_labels': distance_labels,
        'distances': distances,
        'hr_labels': hr_labels,
        'heart_rates': heart_rates,
        'pace_labels': pace_labels,
        'paces': paces_decimal,
        'cadence_labels': cadence_labels,
        'cadences': cadences,
        'total_distance': total_distance,
        'average_pace': average_pace,
        'average_hr': average_hr,
        'average_cadence': average_cadence,
        'fastest_hour_display': fastest_hour_display,
        'worst_hour_display': worst_hour_display,
        'heart_rate_range_zone_2': heart_rate_range_zone_2,
        'percentage_in_zone_2': percentage_in_zone_2,
        'workout_routes': json.dumps(routes_per_workout),
        'zone_times_json': json.dumps(zone_times_per_workout),
        'run_dates_json': json.dumps(run_dates),
        'has_data': has_data,
    })


@csrf_exempt
def filter_data(request):
    time_frame = request.POST.get('time_frame')

    if request.user.is_authenticated:
        user_obj = request.user
    else:
        user_obj = User.objects.get(username='demo')

    # Get the most recent workout's start date
    latest_workout_date = RunningWorkoutData.objects.filter(user=user_obj).aggregate(latest_date=Max('start_date'))['latest_date']

    if not latest_workout_date:
        # Handle the case where there are no workouts
        return JsonResponse({'error': 'No workout data available.'})

    # Adjust the filter_date based on the time_frame and the most recent workout date
    if time_frame == 'all':
        filter_date = timezone.now() - timedelta(days=365 * 100)
    elif time_frame == 'yearly':
        filter_date = latest_workout_date - timedelta(days=365)
    elif time_frame == 'monthly':
        filter_date = latest_workout_date - timedelta(days=30)
    elif time_frame == 'weekly':
        filter_date = latest_workout_date - timedelta(days=7)
    else:
        return JsonResponse({'error': 'Invalid time frame.'})

    # Filter the RunningWorkoutData queryset based on the filter date and the user
    workout_data = RunningWorkoutData.objects.filter(user=user_obj, start_date__gte=filter_date)

    # Aggregate the distance run per month
    distance_data = workout_data.annotate(
        month=ExtractMonth('start_date'), 
        year=ExtractYear('start_date')
    ).values('month', 'year').annotate(distance_sum=Sum('distance')).order_by('year', 'month')

    # Convert distance data to a format suitable for Chart.js
    distance_labels = ['{}/{}'.format(d['month'], d['year']) for d in distance_data]
    distances = [float(d['distance_sum']) for d in distance_data]

    # Average heart rate for each run
    heart_rate_data = workout_data.exclude(heart_rate_data__heart_rate__isnull=True).annotate(avg_hr=Round(Avg('heart_rate_data__heart_rate'), output_field=IntegerField())).order_by('start_date')

    # Convert heart rate data to a format suitable for Chart.js
    hr_labels = [hr.start_date.strftime('%Y-%m-%d') for hr in heart_rate_data]
    heart_rates = [hr.avg_hr for hr in heart_rate_data if hr.avg_hr is not None]

    pace_data = workout_data.annotate(
        pace_seconds_per_mile=ExpressionWrapper(F('duration') / F('distance'), output_field=FloatField())
    ).order_by('start_date')

    pace_labels = [workout.start_date.strftime('%Y-%m-%d') for workout in pace_data]
    paces_decimal = [(pace.pace_seconds_per_mile / 60) for pace in pace_data]  # Convert seconds to decimal minutes

    # Calculate cadence for each run
    cadence_data = workout_data.order_by('start_date')

    # Convert cadence data to a format suitable for Chart.js
    cadence_labels = [c.start_date.strftime('%Y-%m-%d') for c in cadence_data]
    cadences = [round(c.cadence) for c in cadence_data]

    # New code for widget data
    total_distance = workout_data.aggregate(total_distance=Coalesce(Sum('distance'), 0, output_field=FloatField()))['total_distance']
    total_distance = round(total_distance, 2)

    # Calculate average pace separately
    average_pace = workout_data.annotate(
        pace=ExpressionWrapper((F('duration')) / (F('distance') ), output_field=FloatField())
    ).aggregate(average_pace=Coalesce(Avg('pace'), 0, output_field=FloatField()))['average_pace']
    
    average_pace_min = int(average_pace)
    average_pace_sec = int((average_pace - average_pace_min) * 60)
    average_pace = f"{average_pace_min}:{average_pace_sec:02d}"

    average_hr = workout_data.aggregate(average_hr=Coalesce(Avg('heart_rate_data__heart_rate'), 0, output_field=FloatField()))['average_hr']
    average_hr = round(average_hr)

   # calculate average cadence
    average_cadence = sum([c.cadence for c in cadence_data]) / len(cadence_data) if cadence_data else 0
    average_cadence = int(average_cadence)

    # **Heart Rate Zones Calculation**
    max_heart_rate_query = HeartRateData.objects.filter(
            user=user_obj,
            workout__isnull=False
        ).aggregate(max_heart_rate=Max('heart_rate'))

    max_heart_rate = max_heart_rate_query.get('max_heart_rate')

    if max_heart_rate:
        heart_rate_zones = get_heart_rate_zones(max_heart_rate)
        zone_times_per_workout = {zone: [0] * workout_data.count() for zone in heart_rate_zones}
        run_dates = []
        total_time_seconds = 0.0
        workout_index = 0
        time_in_zone_2_seconds = 0.0

        zone_2_range = heart_rate_zones['Zone 2']
        zone_2_lower_limit = int((zone_2_range[0] / 100) * max_heart_rate)
        zone_2_upper_limit = int((zone_2_range[1] / 100) * max_heart_rate)
        heart_rate_range_zone_2 = f"{zone_2_lower_limit}-{zone_2_upper_limit} bpm"

        for workout in workout_data:
            run_dates.append(workout.start_date.strftime('%Y-%m-%d'))
            workout_duration_seconds = float(workout.duration) * 60
            total_time_seconds += workout_duration_seconds

            for zone, (lower_pct, upper_pct) in heart_rate_zones.items():
                lower_limit = int((lower_pct / 100) * max_heart_rate)
                upper_limit = int((upper_pct / 100) * max_heart_rate)

                hr_data_in_zone = workout.heart_rate_data.filter(
                    heart_rate__gte=lower_limit,
                    heart_rate__lte=upper_limit,
                    start_date__gte=workout.start_date,
                    end_date__lte=workout.end_date
                )

                workout_time_in_zone_seconds = sum([
                    (data.end_date - data.start_date).total_seconds() for data in hr_data_in_zone
                ])

                zone_times_per_workout[zone][workout_index] += workout_time_in_zone_seconds / 60.0

                if zone == 'Zone 2':
                    time_in_zone_2_seconds += workout_time_in_zone_seconds

            workout_index += 1

        total_workout_minutes = total_time_seconds / 60

        if total_workout_minutes > 0:
            percentage_in_zone_2 = (time_in_zone_2_seconds / total_workout_minutes) * 100
        else:
            percentage_in_zone_2 = 0

        percentage_in_zone_2 = round(percentage_in_zone_2, 2)
    else:
        heart_rate_range_zone_2 = "N/A"

    return JsonResponse({
        'distance_labels': distance_labels,
        'distances': distances,
        'hr_labels': hr_labels,
        'heart_rates': heart_rates,
        'pace_labels': pace_labels,
        'paces': paces_decimal,
        'cadence_labels': cadence_labels,
        'cadences': cadences,
        'total_distance': total_distance,
        'average_pace': average_pace,
        'average_hr': average_hr,
        'average_cadence': average_cadence,
        'zone_times_per_workout': zone_times_per_workout,
        'run_dates': run_dates,
        'heart_rate_range_zone_2': heart_rate_range_zone_2,
        'percentage_in_zone_2': percentage_in_zone_2,
    })


def parse_gpx_file(gpx_file_path):
    """Parse GPX file to extract route data."""
    # Load and parse the GPX file
    tree = ET.parse(gpx_file_path)
    root = tree.getroot()

    # Define GPX and XML namespaces
    gpx_ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

    # Find all track points
    track_points = root.findall('.//gpx:trkpt', gpx_ns)

    route_data = []

    # Iterate over track points and extract lat, lon and elevation (if available)
    for trkpt in track_points:
        lat = trkpt.attrib.get('lat')
        lon = trkpt.attrib.get('lon')
        ele = trkpt.find('gpx:ele', gpx_ns)
        elevation = ele.text if ele is not None else None
        route_data.append({
            'latitude': lat,
            'longitude': lon,
            'elevation': elevation
        })

    return route_data

@login_required
def upload(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            start_time = time.time()  # Start timer
            # Clear existing data for the user
            HeartRateData.objects.filter(user=request.user).delete()
            RunningWorkoutData.objects.filter(user=request.user).delete()
            StepCountData.objects.filter(user=request.user).delete()
            WorkoutRoute.objects.filter(user=request.user).delete()

            running_workouts_bulk = []
            heart_rate_data_bulk = []
            step_count_data_bulk = []
            workout_routes_bulk = []

            if 'exportXML' in request.FILES:
                uploaded_file = request.FILES['exportXML']
                tree = ET.parse(uploaded_file)
                root = tree.getroot()

                # Process running workouts
                for workout in root.findall(".//Workout[@workoutActivityType='HKWorkoutActivityTypeRunning']"):
                    distance = 0
                    for ws in workout.findall(".//WorkoutStatistics"):
                        if ws.attrib["type"] == "HKQuantityTypeIdentifierDistanceWalkingRunning":
                            distance = float(ws.attrib["sum"])
                    if distance < 1:
                        continue
                    metadata_entry = workout.find(".//MetadataEntry[@key='HKIndoorWorkout']")
                    if metadata_entry is not None and metadata_entry.attrib["value"] != '0':
                        continue

                    # Correctly handle duration in seconds
                    duration_in_minutes = float(workout.attrib["duration"])
                    duration_in_seconds = int(duration_in_minutes * 60)

                    source = workout.attrib["sourceName"]
                    start_date = parse(workout.attrib["startDate"])
                    end_date = parse(workout.attrib["endDate"])
                    active_energy_burned = None
                    for ws in workout.findall(".//WorkoutStatistics"):
                        if ws.attrib["type"] == "HKQuantityTypeIdentifierActiveEnergyBurned":
                            active_energy_burned = ws.attrib["sum"]

                    running_workouts_bulk.append(RunningWorkoutData(
                        user=request.user,
                        duration=duration_in_seconds,
                        source=source,
                        start_date=start_date,
                        end_date=end_date,
                        distance=distance,
                        cals_burned=active_energy_burned
                    ))

                # Bulk create running workouts
                RunningWorkoutData.objects.bulk_create(running_workouts_bulk)

                # Process heart rate records
                hr_records = root.findall(".//Record[@type='HKQuantityTypeIdentifierHeartRate']")
                for hr_record in hr_records:
                    hr_value = float(hr_record.attrib["value"])
                    hr_start_date = parse(hr_record.attrib["startDate"])
                    hr_end_date = parse(hr_record.attrib["endDate"])

                    workout = RunningWorkoutData.objects.filter(start_date__lte=hr_start_date, end_date__gte=hr_end_date).first()

                    heart_rate_data_bulk.append(HeartRateData(
                        user=request.user,
                        workout=workout,
                        heart_rate=hr_value,
                        start_date=hr_start_date,
                        end_date=hr_end_date
                    ))

                # Bulk create heart rate data
                HeartRateData.objects.bulk_create(heart_rate_data_bulk)

                # Process step count records
                step_count_records = root.findall(".//Record[@type='HKQuantityTypeIdentifierStepCount']")
                for step_count_record in step_count_records:
                    step_count_value = int(step_count_record.attrib["value"])
                    step_count_start_date = parse(step_count_record.attrib["startDate"])
                    step_count_end_date = parse(step_count_record.attrib["endDate"])

                    workout = RunningWorkoutData.objects.filter(start_date__lte=step_count_start_date, end_date__gte=step_count_end_date).first()

                    step_count_data_bulk.append(StepCountData(
                        user=request.user,
                        workout=workout,
                        step_count=step_count_value,
                        start_date=step_count_start_date,
                        end_date=step_count_end_date
                    ))

                # Bulk create step count data
                StepCountData.objects.bulk_create(step_count_data_bulk)

            # Process GPX files if uploaded
            if 'exportGPX' in request.FILES:
                gpx_zip_file = request.FILES['exportGPX']
                gpx_zip_file_name = default_storage.save('tmp/' + gpx_zip_file.name, ContentFile(gpx_zip_file.read()))
                gpx_zip_file_path = os.path.join(settings.MEDIA_ROOT, gpx_zip_file_name)

                with zipfile.ZipFile(gpx_zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(path=os.path.join(settings.MEDIA_ROOT, 'tmp'))

                for dir_path, dirs, files in os.walk(os.path.join(settings.MEDIA_ROOT, 'tmp')):
                    for filename in files:
                        if filename.endswith('.gpx'):
                            gpx_file_path = os.path.join(dir_path, filename)

                            try:
                                # Extract the date from the filename
                                date_str = filename.split('_')[1]  # The date should be the second element when we split the string by '_'
                                workout_date = datetime.strptime(date_str, "%Y-%m-%d").date()  # Convert the date string to a datetime.date object
                            except ValueError:
                                print(f"Unable to extract date from filename: {filename}. Skipping file.")
                                continue

                            workout = RunningWorkoutData.objects.filter(user=request.user, start_date__date=workout_date).first()
                            if not workout:
                                continue
                            
                            # Parse GPX file
                            tree = ET.parse(gpx_file_path)
                            root = tree.getroot()
                            gpx_ns = {"gpx": "http://www.topografix.com/GPX/1/1"}
                            track_points = root.findall('.//gpx:trkpt', gpx_ns)

                            for trkpt in track_points:
                                lat = trkpt.attrib.get('lat')
                                lon = trkpt.attrib.get('lon')
                                ele = trkpt.find('gpx:ele', gpx_ns)
                                elevation = ele.text if ele is not None else None

                                workout_routes_bulk.append(WorkoutRoute(
                                    user=request.user,
                                    workout=workout,
                                    latitude=lat,
                                    longitude=lon,
                                    elevation=elevation
                                ))

                WorkoutRoute.objects.bulk_create(workout_routes_bulk)

                shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'tmp'))
                os.makedirs(os.path.join(settings.MEDIA_ROOT, 'tmp'), exist_ok=True)

                end_time = time.time()  # End timer
                total_time = end_time - start_time
                print(f"File upload and processing took: {total_time} seconds.")

            return redirect('home')
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})



def tables(request):
    return render(request, 'tables.html')


def workouts(request):
    if request.user.is_authenticated:
        user_obj = request.user
    else:
        user_obj = User.objects.get(username='demo')
    
    # Start with a base queryset that only includes workouts for the current user
    base_queryset = RunningWorkoutData.objects.filter(user=user_obj)
    form = WorkoutFilterForm(request.GET)

    if form.is_valid():
        filter_q = Q()  # Initialize an empty Q object for additional filters
        year = form.cleaned_data.get('year')
        month = form.cleaned_data.get('month')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        distance_range = form.cleaned_data.get('distance_range')
        
        # Apply filters based on the form inputs
        if year:
            filter_q &= Q(start_date__year=year)
        if month:
            filter_q &= Q(start_date__month=month)
        if start_date:
            filter_q &= Q(start_date__gte=start_date)
        if end_date:
            filter_q &= Q(end_date__lt=end_date + timedelta(days=1))
        if distance_range:
            if distance_range == '5k':
                filter_q &= Q(distance__gte=3.1 - 0.1, distance__lte=3.1 + 0.5)
            elif distance_range == '10k':
                filter_q &= Q(distance__gte=6.2 - 0.1, distance__lte=6.2 + 0.5)
            elif distance_range == 'half_marathon':
                filter_q &= Q(distance__gte=13.1 - 0.1, distance__lte=13.1 + 0.5)
            elif distance_range == 'marathon':
                filter_q &= Q(distance__gte=26.2 - 0.1, distance__lte=26.2 + 0.5)
        
        # Use the base queryset and apply additional filters
        workout_data = base_queryset.filter(filter_q).annotate(
            avg_hr=Round(Avg('heart_rate_data__heart_rate'), output_field=IntegerField())
        )
    else:
        # If the form is not valid or not submitted, use the base queryset
        workout_data = base_queryset

    # Process the workout_data for display
    for workout in workout_data:
        # Assume workout.duration is already in total seconds
        total_seconds = int(workout.duration)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Format the duration
        if hours:
            workout.display_duration = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            workout.display_duration = f"{minutes:02d}:{seconds:02d}"


    context = {
        'workout_data': workout_data,
        'form': form,
        'data_exists': workout_data.exists(),
    }

    # Optional: Debugging prints
    # print("Current user:", request.user)
    # print("QuerySet:", workout_data.query)

    return render(request, 'workouts.html', context)


def workout_detail(request, workout_id):
    if request.user.is_authenticated:
        user_obj = request.user
    else:
        user_obj = User.objects.get(username='demo')

    workout = get_object_or_404(RunningWorkoutData, pk=workout_id, user=user_obj)

    # Query the heart rate data for this workout
    heart_rates = workout.heart_rate_data.all()

    # Calculate the average heart rate
    avg_heart_rate = heart_rates.aggregate(Avg('heart_rate'))['heart_rate__avg']

    # Round to nearest whole number
    avg_heart_rate = round(avg_heart_rate)
    
    # Convert the duration to HH:MM:SS format
    total_seconds = int(workout.duration)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format the duration
    if hours:
        duration_formatted = f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        duration_formatted = f"{minutes:02d}:{seconds:02d}"

    workout.display_duration = duration_formatted  # Use a new attribute for the formatted duration
    
    # Convert the cals_burned to integer
    cals_burned = int(float(workout.cals_burned) + 0.5)

    return render(request, 'workout_detail.html', {
        'workout': workout, 
        'avg_heart_rate': avg_heart_rate, 
        'duration': workout.display_duration,  # Use the formatted duration
        'cals_burned': cals_burned
    })


def charts(request):
    # Retrieve the duration, distance, and calories burned for the most recent 3 workouts
    recent_workouts = RunningWorkoutData.objects.order_by('-start_date')[:3]
    durations = []
    distances = []
    cals_burned = []

    for workout in recent_workouts:
        durations.append(float(workout.duration))
        distances.append(float(workout.distance) if workout.distance else 0)
        cals_burned.append(float(workout.cals_burned)
                           if workout.cals_burned else 0)

    # Pass the values to the template as context
    context = {
        'durations': durations,
        'distances': distances,
        'cals_burned': cals_burned,
    }
    return render(request, 'charts.html', context)



 
