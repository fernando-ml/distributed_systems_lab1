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
    usage_percentage = (load / cpu_count) * 100
    return min(usage_percentage, 100)  # cap at 100%

# Example usage
cpu_status = get_cpu_status()
print(f"1-minute load average: {cpu_status['lavg_1']:.2f}%")
print(f"5-minute load average: {cpu_status['lavg_5']:.2f}%")
print(f"15-minute load average: {cpu_status['lavg_15']:.2f}%")