import os
import json

from src.ingestion.analyzer import analyze_codebase
import os
import shutil
import stat
from git import Repo
from src.config import *

class RepoLoader:
    
    def load(self, repo_url):
   
        if not repo_url:
            print("No URL provided.")
            exit()

        path_url = REPO_PATH
        
        def remove_readonly(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        
        if os.path.exists(path_url):
            print(f"Cleaning up existing data at {path_url}...")
            shutil.rmtree(path_url, onexc=remove_readonly)
        print(f" [Repo Loader] => Cloning {repo_url}...")
        
        try:
            Repo.clone_from(repo_url, path_url, depth=1)
            print('[Repo Loader] => Repo loaded successfully!!!')
            
        except Exception as e:
            print(f" [Repo Loader] => Error cloning repo: {e}")
            raise

        
        if not os.path.exists(REPO_PATH):
            print(f"Error: Path '{REPO_PATH}' does not exist.")
        else:
            data = analyze_codebase(REPO_PATH)
            
            with open(INPUT_FILE, "w") as f:
                json.dump(data, f, indent=2)

            print(f"   Graph saved to {INPUT_FILE}")
            print(f"   Files: {data['stats']['files']}")
            print(f"   Definitions: {data['stats']['definitions']}")
            print(f"   Calls/Edges: {data['stats']['calls']}")
