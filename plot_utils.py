import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

def generate_plots(job_assignments, job_completions, load_balancing_algorithm):
    # Merge assignment and completion logs
    jobs = []
    for assignment in job_assignments:
        job_id = assignment['job_id']
        worker_id = assignment['worker_id']
        time_assigned = assignment['time_assigned']
        cpu_usage = assignment['cpu_usage']
        # Find the completion for this job
        completion = next((comp for comp in job_completions if comp['job_id'] == job_id), None)
        if completion:
            time_completed = completion['time_completed']
            duration = time_completed - time_assigned
        else:
            time_completed = None
            duration = None
        jobs.append({
            'job_id': job_id,
            'worker_id': worker_id,
            'time_assigned': time_assigned,
            'time_completed': time_completed,
            'duration': duration,
            'cpu_usage': cpu_usage
        })
    # Generate plots
    # Job Durations per Worker
    job_ids = [job['job_id'] for job in jobs]
    durations = [job['duration'] for job in jobs]
    worker_ids = [job['worker_id'] for job in jobs]

    # Assign a color to each worker
    worker_list = list(set(worker_ids))
    worker_colors = {}
    color_palette = ['blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'gray', 'olive', 'cyan']
    for i, worker_id in enumerate(worker_list):
        worker_colors[worker_id] = color_palette[i % len(color_palette)]

    bar_colors = [worker_colors[worker_id] for worker_id in worker_ids]

    plt.figure(figsize=(10, 6))
    plt.bar(job_ids, durations, color=bar_colors)
    plt.xlabel('Job ID')
    plt.ylabel('Duration (s)')
    plt.title(f'Job Durations by Worker ({load_balancing_algorithm})')
    
    # workers' legend
    legend_elements = [Line2D([0], [0], color=color, lw=4, label=f'Worker {worker_id}')
                       for worker_id, color in worker_colors.items()]
    plt.legend(handles=legend_elements)
    plt.savefig(f'job_durations_{load_balancing_algorithm}.png')
    plt.close()

    # CPU Usage vs. job duration per worker
    cpu_usages = [job['cpu_usage'] for job in jobs]
    durations_filtered = [dur for dur, cpu in zip(durations, cpu_usages) if cpu is not None]
    cpu_usages_filtered = [cpu for cpu in cpu_usages if cpu is not None]
    worker_ids_filtered = [wid for wid, cpu in zip(worker_ids, cpu_usages) if cpu is not None]

    plt.figure(figsize=(10, 6))
    for worker_id in worker_list:
        worker_cpu = [cpu for cpu, wid in zip(cpu_usages_filtered, worker_ids_filtered) if wid == worker_id]
        worker_duration = [dur for dur, wid in zip(durations_filtered, worker_ids_filtered) if wid == worker_id]
        plt.scatter(worker_cpu, worker_duration, color=worker_colors[worker_id], label=f'Worker {worker_id}')
    plt.xlabel('CPU Usage (lavg_1)')
    plt.ylabel('Duration (s)')
    plt.title(f'CPU Usage vs Job Duration ({load_balancing_algorithm})')
    plt.legend()
    plt.savefig(f'cpu_vs_duration_{load_balancing_algorithm}.png')
    plt.close()

    # distribution plot CPU usage for all workers
    cpu_usages_all = [cpu for cpu in cpu_usages if cpu is not None]
    plt.figure(figsize=(10, 6))
    plt.hist(cpu_usages_all, bins=10, color='skyblue', edgecolor='black')
    plt.xlabel('CPU Usage (lavg_1)')
    plt.ylabel('Frequency')
    plt.title(f'Distribution of CPU Usage at Assignment ({load_balancing_algorithm})')
    plt.savefig(f'cpu_usage_distribution_{load_balancing_algorithm}.png')
    plt.close()