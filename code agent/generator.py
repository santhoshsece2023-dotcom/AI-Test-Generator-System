import os
import json
from google import genai
from google.genai.errors import APIError

# Try to initialize the client, it will fail if GEMINI_API_KEY is not set
try:
    client = genai.Client()
except Exception as e:
    client = None
    print(f"Warning: Failed to initialize Google GenAI Client. Is GEMINI_API_KEY set? {e}")

def generate_initial_tests(source_code: str, analysis_metadata: dict) -> str:
    """Generates initial test functions using Gemini."""
    if not client:
         return "# Error: GEMINI_API_KEY is not set in the environment or client failed to initialize."
         
    prompt = f"""
    You are an expert Python test engineer. 
    Write robust `pytest` test cases for the following python code.
    
    Code Analysis Metadata (JSON):
    {json.dumps(analysis_metadata, indent=2)}
    
    Source Code:
    ```python
    {source_code}
    ```
    
    Requirements:
    1. Write unit tests for each function and class method.
    2. Write integration tests if functions call each other.
    3. Include edge cases (boundary values, invalid inputs, exceptions).
    4. Use `pytest.raises` for expected exceptions.
    5. Mock dependencies appropriately using `unittest.mock`.
    6. Return ONLY the raw valid Python code. Do not include markdown formatting like ```python, just the raw code.
    7. Ensure you import pytest and the necessary modules. Suppose the functions are inside a python file named `target_module.py` and can be imported directly.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        # Strip potential markdown formatting if the LLM ignores the instruction
        code = response.text
        if code.startswith("```python"):
             code = code[9:]
        if code.startswith("```"):
             code = code[3:]
        if code.endswith("```"):
             code = code[:-3]
        return code.strip()
    except Exception as e:
        return f"# Error generating tests: {str(e)}"
        

def refine_tests_with_coverage(source_code: str, existing_tests: str, uncovered_statements: list) -> str:
    """Refines tests when lines are uncovered."""
    if not client:
         return existing_tests + "\n# Error: Could not refine. GEMINI_API_KEY missing."
         
    prompt = f"""
    You are an expert Python test engineer. 
    The current tests do not cover some lines of the source code.
    Please generate *additional* `pytest` test functions to cover these missing lines.
    
    Source Code:
    ```python
    {source_code}
    ```
    
    Existing Tests:
    ```python
    {existing_tests}
    ```
    
    Uncovered Lines / Statements (Line numbers or context):
    {json.dumps(uncovered_statements)}
    
    Requirements:
    1. Output ONLY the new test functions (raw python code, no markdown ```).
    2. Do NOT output the existing tests.
    3. Ensure they use properly named functions starting with `test_`.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        code = response.text
        if code.startswith("```python"):
             code = code[9:]
        if code.startswith("```"):
             code = code[3:]
        if code.endswith("```"):
             code = code[:-3]
        return code.strip()
    except Exception as e:
        return f"# Error refining tests: {str(e)}"
