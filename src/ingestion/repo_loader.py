import os
import shutil
import stat
from git import Repo

class RepoLoader:
    def __init__(self, repo_url: str) -> None:
        self.repo_url = repo_url
        
    def load(self, path_url: str) -> None:
        """Clones the Git repo to local path."""
        
        def remove_readonly(func, path, exc_info):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        
        if os.path.exists(path_url):
            print(f"Cleaning up existing data at {path_url}...")
            shutil.rmtree(path_url, onexc=remove_readonly)
        print(f" [Repo Loader] => Cloning {self.repo_url}...")
        
        try:
            Repo.clone_from(self.repo_url, path_url, depth=1)
            print('[Repo Loader] => Repo loaded successfully!!!')
            
        except Exception as e:
            print(f" [Repo Loader] => Error cloning repo: {e}")
            raise