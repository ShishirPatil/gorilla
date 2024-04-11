"""
    This module will handle all filesystem interactions
    The FSManager class is the base class for all filesystem managers
"""
import os
import subprocess

class FSManager:
    """Base class for all FS operations.

    Attributes:
        fs_path (type): path to the fs location.

    Methods:
        execute: Execute command
        commit: Commit SQL calls
        revert: "Revert changes to previous commit through git LFS
        initialize_git_lfs: Initialize the current directory as a git lfs repo if it isn't already
    """
    def __init__(self, fs_path=None, git_init=True):
        """Initialize the FSManager.
        
        Args:
            fs_path (str): path to the fs path. Default is CWD
        """
        if not fs_path:
            self.fs_path = os.getcwd()
        else:
            self.fs_path = os.path.abspath(fs_path)
            if not os.path.exists(self.fs_path) or not os.path.isdir(self.fs_path):
                raise Exception("Please provide a valid directory")
            
        self.is_git_repo = os.path.exists(os.path.join(self.fs_path, '.git'))
        self.git_init = git_init

    def execute(self, command: str, display=False):
        """Execute command.
        
        Args:
            command (str): Command to execute.
        """
        if display:
            return subprocess.call(command, shell=True, cwd=self.fs_path)
        return subprocess.call(command, shell=True, cwd=self.fs_path, stdout=subprocess.DEVNULL)
    
    def commit(self, message='Auto-commit via FSManager', clean=True):
        """Commit all current changes through git LFS"""
        try:
            self.execute(f'git add .')  # Stage all changes
            self.execute(f'git commit -m "{message}"')  # Commit with a message
            if clean and not self.is_git_repo:
                self.execute('rm -rf .git')  # Remove git once commit happens to save space
        except Exception as e:
            print(f"Error during commit: {e}")
    
    def revert(self, clean=True):
        """Revert changes to previous commit through git LFS"""
        try:
            self.execute('git clean -fd')
            self.execute('git reset --hard HEAD')
            if clean and not self.is_git_repo:
                self.execute('rm -rf .git')  # Remove git once revert happens to save space
        except Exception as e:
            print(f"Error during revert: {e}")
    
    def initialize_version_control(self):
        """Initialize the current directory as a git lfs repo if it isn't already."""
        if self.git_init:
            if not os.path.exists(os.path.join(self.fs_path, '.git')):
                try:
                    self.execute('git init')  # Initialize git repository
                    if self._exceed_directory_size(os.getcwd()):
                        self.execute('git lfs install')  # Initialize git LFS
                        print("Initialized current directory as a Git LFS repository.")
                    self.execute('git add .')
                    self.execute("git commit --allow-empty -n -m init")
                except Exception as e:
                    print(f"Error during Git initialization: {e}")
            else:
                # check to see if there are uncommitted changes
                uncommitted = self._check_uncommitted_changes()
                if uncommitted:
                    raise Exception("Please commit or stash all changes before executing FS commands")
            

    def task_to_prompt(self, task_description, forward=True):
        """
        Formats a prompt for GPT-4 including the directory tree and a user task description.

        :param directory_tree: A nested dictionary representing the directory structure.
        :param task_description: A string describing the task to be performed.
        :return: A formatted string prompt.
        """

        tree_summary = self._get_directory_tree()

        prompt = (
                "Given the following project directory structure:\n"
                f"{tree_summary}\n\n"
        )
        
        # Format the full prompt including the directory structure and the task description
        if forward:
            prompt += (
                "Perform the following task:\n"
                f"{task_description}\n\n"
                "Generate the command to achieve this and only include the shell command as a shell codeblock in the response, "
            )
        else:
            prompt += (
                "Given this shell command:\n"
                f"{task_description}\n\n"
                "Generate the reverse command to reverse the given shell command and only include the shell command as a shell codeblock in the response, "
            )
        prompt += "make sure to not change CWD:"
        return prompt

    def _get_directory_tree(self):
        """
        Creates a nested dictionary that represents the folder structure of self.fs_path.
        """
        summary_lines = []

        # Ensure the self.fs_path ends with a separator to correctly calculate depth
        if not self.fs_path.endswith(os.sep):
            self.fs_path += os.sep

        for root, dirs, files in os.walk(self.fs_path):
            if '.git' in dirs:
                dirs.remove('.git')
            # Calculate the depth based on the difference between root and self.fs_path
            depth = root.replace(self.fs_path, '').count(os.sep)
            indent = "    " * depth  # Four spaces per indentation level

            # Extract the last part of the root path to get the current directory name
            dirname = os.path.basename(root.rstrip(os.sep))
            if depth > 0:  # Avoid including the self.fs_path itself as a directory line
                summary_lines.append(f"{indent}+ {dirname}/")

            for name in sorted(dirs + files):
                if name in dirs:
                    # Directories will be processed in subsequent iterations of os.walk
                    continue
                else:
                    # Append files directly
                    summary_lines.append(f"{indent}    - {name}")

        return "\n".join(summary_lines)

    def _exceed_directory_size(self, path, size_limit=200):
        """size_limit is measured in MB"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
                    if total_size >= size_limit * 1024 * 1024:
                        return True
        return False
    
    def _check_uncommitted_changes(self):
        # Ensure the path exists and is a directory
        if not os.path.isdir(self.fs_path):
            print(f"The path {self.fs_path} is not a valid directory.")
            return

        try:
            result = subprocess.run(["git", "status", "--porcelain"], cwd=self.fs_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Check if the output is empty. If it's not, there are uncommitted changes.
            if result.stdout.strip():
                print("There are uncommitted changes or untracked files.")
                return True
            else:
                return False
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return True

