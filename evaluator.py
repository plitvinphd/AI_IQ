# evaluator.py

import re
import unicodedata

def remove_non_printable(s):
    return ''.join(c for c in s if unicodedata.category(c)[0] != 'C')

def normalize_unicode(s):
    return unicodedata.normalize('NFKC', s)

class Evaluator:
    """
    Evaluates the model's response based on the task type.
    """
    def __init__(self, task_type, expected_output, evaluation_method='algorithmic', evaluator_model_manager=None, evaluator_prompt=None):
        self.task_type = task_type
        self.expected_output = expected_output.strip()
        self.evaluation_method = evaluation_method.lower()
        self.evaluator_model_manager = evaluator_model_manager
        self.evaluator_prompt = evaluator_prompt  # Custom evaluator prompt
        self.log_messages = []  # For logging differences

    def evaluate(self, response):
        response = response.strip()
        if self.evaluation_method == 'algorithmic':
            return self.algorithmic_evaluate(response)
        elif self.evaluation_method == 'llm':
            return self.llm_evaluate(response)
        else:
            # Default to False if evaluation method is unknown
            return False

    def algorithmic_evaluate(self, response):
        if self.task_type == "string_match":
            # Normalize Unicode and remove non-printable characters
            expected_normalized = normalize_unicode(remove_non_printable(self.expected_output))
            response_normalized = normalize_unicode(remove_non_printable(response))

            # Process the expected output
            expected_lines = expected_normalized.splitlines()
            expected_words = [word.strip().lower() for word in expected_lines if word.strip()]

            # Process the actual response
            actual_lines = response_normalized.splitlines()
            actual_words = [word.strip().lower() for word in actual_lines if word.strip()]

            # Compare the lists
            if expected_words == actual_words:
                return True
            else:
                # Log differences
                missing_in_response = set(expected_words) - set(actual_words)
                extra_in_response = set(actual_words) - set(expected_words)
                log_message = f"Words missing in response: {missing_in_response}\nExtra words in response: {extra_in_response}"
                self.log_messages.append(log_message)
                return False
        elif self.task_type == "entity_recognition":
            expected_entities = set(re.findall(r'\b\w+\b', self.expected_output.lower()))  # Extract words as entities
            response_entities = set(re.findall(r'\b\w+\b', response.lower()))
            
            # Check if response contains at least the expected entities
            missing_entities = expected_entities - response_entities
            extra_entities = response_entities - expected_entities
            
            if not missing_entities:  # If all expected entities are in response
                return True
            else:
                log_message = f"Missing entities: {missing_entities}\nExtra entities in response: {extra_entities}"
                self.log_messages.append(log_message)
                return False

    def llm_evaluate(self, response):
        if not self.evaluator_model_manager:
            raise ValueError("Evaluator ModelManager is not provided for LLM evaluation.")

            # Use the custom evaluator prompt if provided, otherwise use the default
        if self.evaluator_prompt and self.evaluator_prompt.strip():
            evaluation_prompt = self.evaluator_prompt.format(
                task_type=self.task_type,
                expected_output=self.expected_output,
                response=response
            )
        else:
            # Default evaluation prompt
            evaluation_prompt = f"""
        You are an expert evaluator. Compare the following expected output and actual response, and determine if the response meets the expectations for the task '{self.task_type}'.

        ### Expected Output:
        {self.expected_output}

        ### Actual Response:
        {response}

        Based on the expected output and the actual response, does the response meet the expectations? Reply with 'Yes' if it meets the expectations, or 'No' if it does not, followed by a brief explanation.
        """

            # Generate evaluation using the evaluator LLM
        evaluation_result = self.evaluator_model_manager.generate_response(evaluation_prompt)

        # Process the evaluation result
        if 'yes' in evaluation_result.lower():
            return True
        else:
            # Log the evaluator's explanation
            self.log_messages.append(evaluation_result.strip())
            return False
