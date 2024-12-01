# trial_manager.py

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from metrics_logger import MetricsLogger
import streamlit as st

class TrialManager:
    """
    Manages running multiple trials concurrently.
    """
    def __init__(self, model_manager, evaluator, num_trials=50, max_workers=5, prompt='', **kwargs):
        self.model_manager = model_manager
        self.evaluator = evaluator
        self.num_trials = num_trials
        self.max_workers = max_workers
        self.prompt = prompt
        self.kwargs = kwargs  # Additional arguments for generate_response
        self.metrics_logger = MetricsLogger()
        self.log_messages = []

    def run_trial(self):
        """
        Run a single trial.
        """
        start_time = time.time()
        response = self.model_manager.generate_response(self.prompt, **self.kwargs)
        end_time = time.time()
        is_correct = self.evaluator.evaluate(response)
        response_time = end_time - start_time
        log_message = '\n'.join(self.evaluator.log_messages)
        self.evaluator.log_messages.clear()  # Clear after use
        self.metrics_logger.log_trial({
            'correct': is_correct,
            'response_time': response_time,
            'response': response,
            'expected_output': self.evaluator.expected_output,
            'evaluation_log': log_message  # Include evaluation log
        })
        return is_correct, response_time

    def run_trials(self):
        """
        Run multiple trials concurrently.
        """
        total_trials = self.num_trials
        completed_trials = 0
        progress_bar = st.progress(0)  # Initialize progress bar
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.run_trial) for _ in range(self.num_trials)]
            for future in as_completed(futures):
                try:
                    future.result()
                    completed_trials += 1
                    # Update progress bar
                    progress = completed_trials / total_trials
                    progress_bar.progress(progress)
                except Exception as e:
                    print(f"Error during trial: {e}")
