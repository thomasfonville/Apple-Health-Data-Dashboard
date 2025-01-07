document.addEventListener("DOMContentLoaded", function() {
    var rows = document.getElementsByClassName('clickable-row');

    for (var i = 0; i < rows.length; i++) {
        rows[i].addEventListener('click', function() {
            window.location = this.dataset.href;
        });
    }
});

document.querySelectorAll('input[name="time_frame"]').forEach(function(radioButton) {
    radioButton.addEventListener('change', function(event) {
        var timeFrame = event.target.value;
        var csrftoken = document.querySelector('[name=csrf-token]').content;

        $.ajax({
            url: '/filter_data/',
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            data: {
                'time_frame': timeFrame
            },
            success: function(data) {
                paceChart.data.labels = data.pace_labels;
                paceChart.data.datasets[0].data = data.paces;
                paceChart.update();

                hrChart.data.labels = data.hr_labels;
                hrChart.data.datasets[0].data = data.heart_rates;
                hrChart.update();

                distanceChart.data.labels = data.distance_labels;
                distanceChart.data.datasets[0].data = data.distances;
                distanceChart.update();

                cadenceChart.data.labels = data.cadence_labels;
                cadenceChart.data.datasets[0].data = data.cadences;
                cadenceChart.update();

                // Update widgets
                $('#total-distance').text(data.total_distance + ' mi');
                $('#average-pace').text(data.average_pace + ' per mile');
                $('#average-hr').text(data.average_hr + ' bpm');
                $('#average-cadence').text(data.average_cadence + ' spm');
                $('#heart-rate-zone-2').text(data.heart_rate_range_zone_2);
                $('#zone-2-time').text(data.percentage_in_zone_2 + '%');

                // Update heart rate zones chart
                hrZonesChart.data.labels = data.run_dates;
                Object.keys(data.zone_times_per_workout).forEach((zone, index) => {
                    hrZonesChart.data.datasets[index].data = data.zone_times_per_workout[zone];
                });
                hrZonesChart.update();
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});
