import os
import src.config as config

class FileReader:
    def __init__(self):
        self.root_path = os.path.abspath(config.REPO_PATH)
        print(f"[File Reader] =>  Root: {self.root_path}")

    def _get_safe_path(self, file_path):
        """Helper to safely join paths."""
        clean = file_path.replace("\\", "/")
        if clean.startswith("./temp_repo/"):
            clean = clean.replace("./temp_repo/", "", 1)
        elif clean.startswith("temp_repo/"):
            clean = clean.replace("temp_repo/", "", 1)
            
        clean = clean.lstrip("./").lstrip("/")
        return os.path.join(self.root_path, clean)

    def read_file(self, file_path: str, start_line=1, end_line=None, with_lines=True):
        """
        Reads a file safe with line numbers.
        """
        
        try:
            full_path = self._get_safe_path(file_path)

            if not full_path.startswith(self.root_path):
                 return f"Error: Access denied. {file_path} is outside the repository."

            if not os.path.exists(full_path):
                return f"Error: File '{file_path}' not found."

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            if end_line is None:
                end_line = len(lines)

            start_line = max(1, start_line) 
            end_line = min(len(lines), end_line)

            if start_line > end_line:
                print ('[File reader] => Error: Start line is after end line.')
                return "Error: Start line is after end line"

            MAX_LINES = 2000
            
            if (end_line - start_line) > MAX_LINES:
                return (
                    f"Error: File is too large ({len(lines)} lines). You requested {MAX_LINES} lines.\n"
                    f"Reading this much code will overload your memory.\n\n"
                    f"STRATEGY: Use 'structure_inspector_tool' to see the functions inside this file.\n"
                    f"Then, request specifically the lines of the function you care about.\n"
                    f"Note: The Node id = file::{file_path}"
                )

            selected_lines = lines[start_line-1 : end_line]

            if with_lines:
                with_num = []
                for i, line in enumerate(selected_lines):
                    num = start_line + i
                    with_num.append(f"{num:4d} | {line.rstrip()}")
                return "\n".join(with_num)
            else:
                return "".join(selected_lines)

        except Exception as e:
            return f"Error reading file: {str(e)}"

    def list_files(self):
        """Generates a file tree structure."""
        file_tree = []
        
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if d not in config.IGNORE_DIRS and not d.startswith(".")]
            
            rel_path = os.path.relpath(root, self.root_path)
            if rel_path == ".":
                level = 0
            else:
                level = rel_path.count(os.sep) + 1

            indent = ' ' * 4 * level
            file_tree.append(f"{indent}{os.path.basename(root)}/")
            
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                 if f.endswith('.py') or f.endswith('.md'): 
                    file_tree.append(f"{subindent}{f}")
            
            if len(file_tree) > 100: 
                file_tree.append(f"{subindent}... (List truncated)")
                break 

        return "\n".join(file_tree)