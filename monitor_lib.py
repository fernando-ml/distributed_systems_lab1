import os

def get_cpu_status(path='/proc/loadavg'):
    loadavg = {}
    cpu_count = os.cpu_count()

    with open(path, 'r') as f1:
        list_content = f1.read().split()
        
        loadavg['lavg_1'] = calculate_percentage(float(list_content[0]), cpu_count)
        loadavg['lavg_5'] = calculate_percentage(float(list_content[1]), cpu_count)
        loadavg['lavg_15'] = calculate_percentage(float(list_content[2]), cpu_count)

    return loadavg

def calculate_percentage(load, cpu_count):
    usage_percentage = (load / cpu_count)
    return min(usage_percentage, 1.00)  # cap at 100%