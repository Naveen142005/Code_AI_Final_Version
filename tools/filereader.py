import os
from langchain_core.tools import tool
import config

class FileReader:
    def __init__(self):
        self.root_path = os.path.abspath(config.REPO_PATH)
        print(f"[File Reader] =>  Root: {self.root_path}")

    def read_file(self, file_path:str, start_line=1, end_line=None, with_lines=True):
        """
        Reads a file safe with line numbers.
        """
        
        try:
           
            if not file_path.startswith('./temp_repo/'):
                file_path = './temp_repo/' + file_path
                
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
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
                # print (f'[File reader] => f"Error: request too large ({end_line - start_line} lines)')
                return (
                f"Error: File is too large ({len(lines)} lines). You requested {MAX_LINES} lines.\n"
                f"Reading this much code will overload your memory.\n\n"
                f"STRATEGY: Use 'structure_inspector_tool' to see the functions inside this file.\n"
                f"Then, request specifically the lines of the function you care about."
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

        except FileNotFoundError:
            return f"Error: File '{file_path}' not found."
        except ValueError as e:
            return str(e)
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def list_files(self):
        """Generates a file tree structure."""
        file_tree = []
        
        if not self.root_path.startswith('./temp_repo/'):
                self.root_path = './temp_repo/' + self.root_path
                
        for root, dirs, files in os.walk(self.root_path):
            # Ignore hidden folders
            dirs[:] = [d for d in dirs if d not in config.IGNORE_DIRS]
            
            level = root.replace(self.root_path, '').count(os.sep)
            indent = ' ' * 4 * (level)
            file_tree.append(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                if f.endswith('.py'):
                    file_tree.append(f"{subindent}{f}")
        
        return "\n".join(file_tree[:100]) #limit to top 100 items to avoid token overflow