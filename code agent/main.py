import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import analyzer
import generator
import runner

app = FastAPI(title="AI Test Generator")

# Serve static files for UI
if not os.path.exists("static"):
    os.makedirs("static")
    
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/generate-tests")
async def process_code(file: UploadFile = File(...)):
    # 1. Read file
    content = await file.read()
    source_code = content.decode("utf-8")
    
    # 2. Analyze code
    analysis_metadata = analyzer.analyze_code(source_code)
    if "error" in analysis_metadata:
        return {"status": "error", "message": analysis_metadata["error"]}

    # 3. Generate initial tests
    test_code = generator.generate_initial_tests(source_code, analysis_metadata)
    if test_code.startswith("# Error"):
        return {"status": "error", "message": test_code, "test_code": test_code, "analysis": analysis_metadata}
        
    # 4. Run tests and get coverage
    metrics = runner.execute_tests(source_code, test_code, source_filename="target_module.py")
    
    # 5. Feedback Loop: if coverage < 100% and there are missing lines, refine tests once
    iteration = 0
    max_iterations = 1 # Keep it to 1 iteration for MVP
    
    while metrics["percent_covered"] < 100.0 and len(metrics["missing_lines"]) > 0 and iteration < max_iterations:
        new_tests = generator.refine_tests_with_coverage(source_code, test_code, metrics["missing_lines"])
        if new_tests and not new_tests.startswith("# Error"):
            # Append new tests to existing test code
            test_code = test_code + "\n\n" + new_tests
            # Rerun metrics
            metrics = runner.execute_tests(source_code, test_code, source_filename="target_module.py")
        iteration += 1

    return {
        "status": "success",
        "analysis": analysis_metadata,
        "test_code": test_code,
        "coverage": metrics["percent_covered"],
        "missing_lines": metrics["missing_lines"],
        "logs": metrics["output_log"]
    }

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = "static/index.html"
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>UI not found. Please create static/index.html</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
