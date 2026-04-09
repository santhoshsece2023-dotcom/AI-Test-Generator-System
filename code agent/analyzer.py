import ast

def analyze_code(source_code: str) -> dict:
    """
    Analyzes Python source code using AST and extracts meaningful metadata.
    Returns a dictionary containing:
    - dependencies (imports)
    - classes (with methods and their control flow)
    - functions (with their control flow)
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {"error": f"SyntaxError: {str(e)}"}

    analysis = {
        "dependencies": [],
        "classes": [],
        "functions": []
    }

    def extract_function_data(func_node):
        control_flow = set()
        for child in ast.walk(func_node):
            if isinstance(child, ast.If):
                control_flow.add("if_else")
            elif isinstance(child, ast.For):
                control_flow.add("for_loop")
            elif isinstance(child, ast.While):
                control_flow.add("while_loop")
            elif isinstance(child, ast.Try):
                control_flow.add("try_except")
            elif isinstance(child, ast.Raise):
                control_flow.add("raise_exception")
        
        args = [arg.arg for arg in func_node.args.args]
        if func_node.args.vararg:
            args.append(f"*{func_node.args.vararg.arg}")
        if func_node.args.kwarg:
            args.append(f"**{func_node.args.kwarg.arg}")
            
        return {
            "name": func_node.name,
            "args": args,
            "control_flow": list(control_flow)
        }

    class CodeVisitor(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                analysis["dependencies"].append(alias.name)
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            if node.module:
                analysis["dependencies"].append(node.module)
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            class_data = {
                "name": node.name,
                "methods": []
            }
            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef):
                    class_data["methods"].append(extract_function_data(body_item))
            analysis["classes"].append(class_data)
            # Do not visit children to avoid global function extraction
            
        def visit_FunctionDef(self, node):
            # Only top level functions are visited this way if we call it from root
            analysis["functions"].append(extract_function_data(node))
            # Do not visit children

    visitor = CodeVisitor()
    
    # We only want to visit top-level nodes to avoid nested functions/methods being globally scoped
    for node in tree.body:
        visitor.visit(node)

    return analysis
