import ast

def safe_name(node):
    """Safely extract the name from AST nodes"""
    
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = safe_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return safe_name(node.func)
    if isinstance(node, ast.Subscript):
        if hasattr(node.slice, 'value'): 
             return safe_name(node.slice.value)
        return safe_name(node.slice)
    return None

def get_docstring(node):
    """Extracts docstring from a node if present"""
    return ast.get_docstring(node) or ""

def calculate_complexity(node):
    """Calculates Complexity (If/For/While count)."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler, ast.With)):
            complexity += 1
    return complexity