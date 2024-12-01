# metrics_logger.py

class MetricsLogger:
    def __init__(self):
        self.trials = []

    def log_trial(self, trial_data):
        self.trials.append(trial_data)

    def export_csv(self, filename='results.csv'):
        import csv
        keys = self.trials[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(self.trials)

