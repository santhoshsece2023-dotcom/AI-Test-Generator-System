import os
import json
import subprocess

OUTPUT_DIR = "test_output"

def execute_tests(source_code: str, test_code: str, source_filename: str = "target_module.py") -> dict:
    """
    Executes the generated tests against the source code using pytest and coverage.
    Returns test outcome, coverage info, and missing lines.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    source_path = os.path.join(OUTPUT_DIR, source_filename)
    test_path = os.path.join(OUTPUT_DIR, "test_generated.py")

    with open(source_path, "w", encoding="utf-8") as f:
        f.write(source_code)
        
    with open(test_path, "w", encoding="utf-8") as f:
        f.write(test_code)

    # Run tests with coverage
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(OUTPUT_DIR)
    
    # Clean previous coverage
    cov_db_path = os.path.join(OUTPUT_DIR, ".coverage")
    if os.path.exists(cov_db_path):
        os.remove(cov_db_path)

    module_name = source_filename.replace(".py", "")

    run_cmd = ["coverage", "run", f"--source={module_name}", "-m", "pytest", "test_generated.py", "-v"]
    result = subprocess.run(run_cmd, cwd=OUTPUT_DIR, capture_output=True, text=True, env=env)
    
    output_log = result.stdout + "\n" + result.stderr
    success = result.returncode == 0

    # Generate coverage json
    json_cmd = ["coverage", "json", "-o", "coverage.json"]
    subprocess.run(json_cmd, cwd=OUTPUT_DIR, capture_output=True, text=True, env=env)

    coverage_json_path = os.path.join(OUTPUT_DIR, "coverage.json")
    
    metrics = {
        "success": success,
        "output_log": output_log[-2000:], # keep reasonable length
        "percent_covered": 0.0,
        "missing_lines": []
    }

    if os.path.exists(coverage_json_path):
        try:
            with open(coverage_json_path, "r", encoding="utf-8") as f:
                cov_data = json.load(f)
            
            # Coverage.json stores files with full paths or relative paths. We look for our module.
            files = cov_data.get("files", {})
            for fname, fdata in files.items():
                if source_filename in fname:
                    metrics["percent_covered"] = fdata.get("summary", {}).get("percent_covered", 0.0)
                    metrics["missing_lines"] = fdata.get("missing_lines", [])
                    break
        except Exception as e:
            metrics["output_log"] += f"\nError parsing coverage: {e}"

    return metrics
