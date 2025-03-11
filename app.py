# app.py
# run locally with: streamlit run app.py

import streamlit as st
from authentication import save_user_credentials, load_user_credentials, verify_password
from model_manager import ModelManager
from evaluator import Evaluator
from trial_manager import TrialManager
import json

def main():
    st.title("LLM Profile Analysis")

    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'username' not in st.session_state:
        st.session_state['username'] = ''

    menu = ["Login", "SignUp"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type='password')
        st.markdown("**Enter your API keys:**")
        openai_api_key = st.text_input("OpenAI API Key", type='password')
        anthropic_api_key = st.text_input("Anthropic API Key", type='password')
        if st.button("Signup"):
            api_keys = {
                'openai': openai_api_key,
                'anthropic': anthropic_api_key
            }
            save_user_credentials(new_user, new_password, api_keys)
            st.success("You have successfully created an account")
            st.info("Go to Login Menu to login")

    elif choice == "Login":
        if st.session_state['logged_in']:
            st.sidebar.write(f"Logged in as {st.session_state['username']}")
            app_body()
        else:
            st.subheader("Login to Your Account")
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            if st.button("Login"):
                user_credentials = load_user_credentials(username)
                if user_credentials and verify_password(user_credentials['password'], password):
                    st.success(f"Logged In as {username}")
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['api_keys'] = user_credentials['api_keys']
                    app_body()
                else:
                    st.warning("Incorrect Username/Password")

def app_body():
    # Model Settings
    st.sidebar.subheader("Model Settings")
    provider = st.sidebar.selectbox("Provider", ["OpenAI", "Anthropic"])
    if provider == "OpenAI":
        model_name = st.sidebar.selectbox("Model Name", [
            "gpt-4.5-preview",
            "gpt-4.5-preview-2025-02-27",
            "o1",
            "o1-mini", 
            "o3-mini",
            "o1-mini-2024-09-12",
            "o1-preview-2024-09-12",
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ])
        api_key = st.session_state['api_keys'].get('openai', '')
    else:
        model_name = st.sidebar.selectbox("Model Name", [
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022"
        ])
        api_key = st.session_state['api_keys'].get('anthropic', '')

    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 1.0)  # Default set to 1.0
    max_tokens = st.sidebar.number_input("Max Tokens", min_value=1, max_value=2048, value=150)

    # Prompt and Task Settings
    st.subheader("Prompt Settings")
    prompt = st.text_area("Enter your prompt here")
    task_type = st.selectbox("Task Type", ["string_match", "entity_recognition"])
    expected_output = st.text_area("Expected Output for Evaluation")

    # Evaluation Settings
    st.subheader("Evaluation Settings")
    evaluation_method = st.selectbox("Evaluation Method", ["Algorithmic", "LLM"])

    evaluator_model_manager = None  # Initialize to None
    evaluator_api_key = ''
    evaluator_prompt = ''  # Initialize evaluator prompt

    if evaluation_method == "LLM":
        evaluator_provider = st.selectbox("Evaluator LLM Provider", ["OpenAI", "Anthropic"])
        # Let the user choose whether to use the existing API key or enter a new one
        use_existing_api_key = st.checkbox("Use existing API key for evaluator LLM", value=True)
        if use_existing_api_key:
            if evaluator_provider == "OpenAI":
                evaluator_api_key = st.session_state['api_keys'].get('evaluator_openai', st.session_state['api_keys'].get('openai', ''))
            else:
                evaluator_api_key = st.session_state['api_keys'].get('evaluator_anthropic', st.session_state['api_keys'].get('anthropic', ''))
        else:
            # Use a different key for evaluator API key
            evaluator_api_key = st.text_input(f"{evaluator_provider} API Key for Evaluator LLM", type='password')
            save_api_key = st.checkbox("Save this API key for future use")

        if evaluator_provider == "OpenAI":
            evaluator_model_name = st.selectbox("Evaluator Model Name", [
                "gpt-4.5-preview",
                "gpt-4.5-preview-2025-02-27",
                "o1",
                "o1-mini", 
                "o3-mini",
                "o1-mini-2024-09-12",
                "o1-preview-2024-09-12",
                "gpt-4o-mini",
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo"
            ])
        else:
            evaluator_model_name = st.selectbox("Evaluator Model Name", [
                "claude-3-5-sonnet-20241022",
                "claude-3-7-sonnet-20250219",
                "claude-3-5-haiku-20241022"
                # Add other Anthropic models suitable for evaluation
            ])
            # Add input for custom evaluator prompt
            # Add input for custom evaluator prompt
        st.subheader("Custom Evaluator Prompt")
        st.markdown(
                "You can customize the evaluator prompt. Use `{task_type}`, `{expected_output}`, and `{response}` as placeholders.")
        evaluator_prompt = st.text_area("Evaluator Prompt", value="""You are an expert evaluator. Compare the following expected output and actual response, and determine if the response meets the expectations for the task '{task_type}'.
            ### Expected Output:
            {expected_output}

            ### Actual Response:
            {response}

            Based on the expected output and the actual response, does the response meet the expectations? Ignore capitalization or ordering errors, unless specifically asked to do so (e.g., alphabetical order, sort in ascending/descending order). Reply with 'Yes' if it meets the expectations, or 'No' if it does not, followed by a brief explanation.
            """)



    # Trial Settings
    num_trials = st.number_input("Number of Trials", min_value=1, max_value=1000, value=50)
    max_workers = st.number_input("Number of Threads", min_value=1, max_value=100, value=5)

    if st.button("Start Trials"):
        if not api_key:
            st.error(f"API key for {provider} is missing.")
            return
        if evaluation_method == "LLM":
            if evaluator_api_key == '':
                st.error(f"API key for evaluator LLM ({evaluator_provider}) is missing.")
                return
            if not use_existing_api_key and save_api_key:
                # Save the evaluator API key
                evaluator_api_key_key = f'evaluator_{evaluator_provider.lower()}'
                st.session_state['api_keys'][evaluator_api_key_key] = evaluator_api_key
                # Update user's credentials
                user_credentials = load_user_credentials(st.session_state['username'])
                user_credentials['api_keys'][evaluator_api_key_key] = evaluator_api_key
                save_user_credentials(st.session_state['username'], user_credentials['password'], user_credentials['api_keys'])
                st.success(f"{evaluator_provider} Evaluator API Key saved.")

        # Prepare additional arguments
        if provider == 'OpenAI':
            kwargs = {
                'temperature': temperature,
                'max_completion_tokens': int(max_tokens),  # For OpenAI
            }
        else:  # For Anthropic
            kwargs = {
                'temperature': temperature,
                'max_tokens': int(max_tokens),
            }

        model_manager = ModelManager(
            model_name=model_name,
            api_key=api_key,
            provider=provider
        )

        if evaluation_method == "LLM":
            evaluator_model_manager = ModelManager(
                model_name=evaluator_model_name,
                api_key=evaluator_api_key,
                provider=evaluator_provider
            )
        else:
            evaluator_model_manager = None

        evaluator = Evaluator(
            task_type,
            expected_output,
            evaluation_method=evaluation_method.lower(),
            evaluator_model_manager=evaluator_model_manager,
            evaluator_prompt=evaluator_prompt  # Pass the custom evaluator prompt
        )

        trial_manager = TrialManager(
            model_manager=model_manager,
            evaluator=evaluator,
            num_trials=int(num_trials),
            max_workers=int(max_workers),
            prompt=prompt,
            **kwargs
        )

        with st.spinner("Running trials..."):
            trial_manager.run_trials()

        st.success("Trials completed")
        trial_manager.metrics_logger.export_csv(filename=f'{st.session_state["username"]}_results.csv')
        st.markdown(get_table_download_link(f'{st.session_state["username"]}_results.csv'), unsafe_allow_html=True)

        # Display the CSV data preview
        import pandas as pd
        df = pd.read_csv(f'{st.session_state["username"]}_results.csv')
        # Calculate metrics
        correct_count = df['correct'].sum() if 'correct' in df.columns else 0
        total_count = len(df)
        correct_percentage = (correct_count / total_count * 100) if total_count > 0 else 0
        
        # Add metrics to dataframe for CSV export
        metrics_df = pd.DataFrame({
            'metric': ['total_trials', 'correct_count', 'correct_percentage'],
            'value': [total_count, correct_count, f'{correct_percentage:.2f}%']
        })
        
        # Append metrics to existing CSV
        with open(f'{st.session_state["username"]}_results.csv', 'a') as f:
            f.write("\n\n# Summary Metrics\n")
        metrics_df.to_csv(f'{st.session_state["username"]}_results.csv', mode='a', index=False)
        
        # Display metrics prominently
        st.subheader("Results Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Trials", total_count)
        with col2:
            st.metric("Correct Responses", int(correct_count))
        with col3:
            st.metric("Success Rate", f"{correct_percentage:.2f}%")
            
        st.subheader("Data Preview")
        st.dataframe(df.head(100)) # Display first 100 rows as a preview


def get_table_download_link(csv_file):
    """
    Generates a link to download the CSV file.
    """
    import base64
    with open(csv_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{csv_file}">Download Results CSV File</a>'
    return href


if __name__ == '__main__':
    main()
