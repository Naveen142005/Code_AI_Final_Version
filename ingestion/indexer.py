# indexer.py
import ast
import os
from collections import defaultdict
from utils import safe_name, get_docstring, calculate_complexity




MAX_FUNCTION_LIMIT = 300  # Lines


class SemanticIndexer(ast.NodeVisitor):
    def __init__(self, file_path, rel_path, global_class_registry):
        self.file_path = file_path
        self.rel_path = rel_path
        self.module_name = rel_path.replace(".py", "").replace(os.sep, ".")
        self.global_class_registry = global_class_registry 

        self.scope_stack = [self.module_name]
        self.definitions = {}
        self.calls = []
        
        self.context_stack = [] 
        self.scope_aliases = defaultdict(dict)
        self.scope_vars = defaultdict(dict)
        self.return_types = {} 
        self.current_class = None

    def _scope(self):
        return ".".join(self.scope_stack)

    def _add_alias(self, name, real):
        self.scope_aliases[self._scope()][name] = real

    def _add_var(self, name, vtype):
        if not vtype: return
        self.scope_vars[self._scope()][name] = vtype

    def _find_alias(self, name):
        temp = list(self.scope_stack)
        while temp:
            scope = ".".join(temp)
            if name in self.scope_aliases.get(scope, {}):
                return self.scope_aliases[scope][name]
            temp.pop()
        return name

    def _find_var_type(self, name):
        temp = list(self.scope_stack)
        while temp:
            scope = ".".join(temp)
            if name in self.scope_vars.get(scope, {}):
                return self.scope_vars[scope][name]
            temp.pop()
        
        # Global Registry Check
        if "." in name:
            obj, attr = name.split(".", 1)
            obj_type = self._find_var_type(obj)
            if obj_type and obj_type in self.global_class_registry:
                 return self.global_class_registry[obj_type].get(attr)
        return None

    def _resolve_import_path(self, module, level):
        if level == 0: return module
        parts = self.module_name.split(".")
        if level > len(parts): return module
        base = ".".join(parts[:-level])
        return f"{base}.{module}" if module else base

 
    def visit_Import(self, node):
        for a in node.names:
            self._add_alias(a.asname or a.name, a.name)

    def visit_ImportFrom(self, node):
        module = self._resolve_import_path(node.module or "", node.level)
        for a in node.names:
            full_name = f"{module}.{a.name}"
            self._add_alias(a.asname or a.name, full_name)

    def visit_ClassDef(self, node):
        full = f"{self._scope()}.{node.name}"
        bases = [safe_name(b) for b in node.bases]

        role = "class"
        if any("Model" in b for b in bases): role = "db_model"
        if any("Exception" in b for b in bases): role = "exception"

        self.definitions[full] = {
            "type": "class",
            "file": self.rel_path,
            "start": node.lineno,
            "end": node.end_lineno,
            "bases": bases,
            "docstring": get_docstring(node),
            "role": role  
        }
        
        prev_class = self.current_class
        self.current_class = full
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()
        self.current_class = prev_class

    def visit_FunctionDef(self, node):
        self._handle_function(node, False)

    def visit_AsyncFunctionDef(self, node):
        self._handle_function(node, True)

    def _handle_function(self, node, is_async):
        full = f"{self._scope()}.{node.name}"
        
        ret_type = safe_name(node.returns) if node.returns else "Unknown"
        if ret_type: ret_type = self._find_alias(ret_type)
        self.return_types[full] = ret_type

        decorators = [safe_name(d) for d in node.decorator_list if safe_name(d)]
        role = "function"
        if any("route" in d or "get" in d or "post" in d for d in decorators): role = "api_endpoint"
        if any("task" in d or "celery" in d for d in decorators): role = "background_task"
        
        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', start_line)
        line_count = end_line - start_line
        complexity = calculate_complexity(node)

        self.definitions[full] = {
            "type": "function",
            "file": self.rel_path,
            "start": start_line,
            "end": end_line,
            "async": is_async,
            "return_type": ret_type,
            "docstring": get_docstring(node),
            "complexity": complexity,  
            "lines": line_count,       
            "is_huge": line_count > MAX_FUNCTION_LIMIT, 
            "decorators": decorators,
            "role": role
        }

        self.scope_stack.append(node.name)
        self.context_stack.append("function") 
        
        # Handle Args
        for arg in node.args.args:
            arg_type = "Unknown"
            if arg.annotation:
                arg_type = self._find_alias(safe_name(arg.annotation))
            if arg.arg == "self" and self.current_class:
                arg_type = self.current_class
            self._add_var(arg.arg, arg_type)

        self.generic_visit(node)
        self.context_stack.pop() 
        self.scope_stack.pop()


    def visit_Try(self, node):
        self.context_stack.append("try_block") 
        self.generic_visit(node)
        self.context_stack.pop()

    def visit_If(self, node):
        self.context_stack.append("condition") 
        self.generic_visit(node)
        self.context_stack.pop()

    def visit_For(self, node):
        self.context_stack.append("loop")      
        self.generic_visit(node)
        self.context_stack.pop()
        
    def visit_While(self, node):
        self.context_stack.append("loop")
        self.generic_visit(node)
        self.context_stack.pop()

    def visit_Assign(self, node):
        vtype = None
        if isinstance(node.value, ast.Call):
            func_name = self._find_alias(safe_name(node.value.func))
            vtype = self.return_types.get(func_name, func_name)
        elif isinstance(node.value, ast.Name):
            vtype = self._find_var_type(node.value.id)

        if vtype:
            for t in node.targets:
                if isinstance(t, ast.Name):
                    self._add_var(t.id, vtype)
                elif isinstance(t, ast.Attribute) and safe_name(t.value) == "self" and self.current_class:
                    if self.current_class not in self.global_class_registry:
                        self.global_class_registry[self.current_class] = {}
                    self.global_class_registry[self.current_class][t.attr] = vtype
        self.generic_visit(node)

    def visit_Call(self, node):
        raw_name = safe_name(node.func)
        scope = self._scope()
        resolved_target = raw_name

        if raw_name:
            alias_target = self._find_alias(raw_name)
            if alias_target != raw_name:
                resolved_target = alias_target
            elif "." in raw_name:
                obj, meth = raw_name.rsplit(".", 1)
                vtype = self._find_var_type(obj)
                if vtype:
                    resolved_target = f"{vtype}.{meth}"

        self.calls.append({
            "source": scope,
            "target_hint": resolved_target,
            "line": node.lineno,
            "context": list(self.context_stack),
            "is_protected": "try_block" in self.context_stack 
        })
        self.generic_visit(node)