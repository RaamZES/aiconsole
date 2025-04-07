from pathlib import Path
from aiconsole.core.project.project import _project_initialized
from aiconsole.core.settings.settings import settings

def init_project(project_path: Path | None = None):
    """
    Initialize project
    
    Args:
        project_path (Path | None): Path to project
    """
    global _project_initialized
    
    if not _project_initialized:
        # Set project path
        if project_path:
            settings.project_path = project_path
        else:
            settings.project_path = Path.cwd()
            
        # Create necessary directories
        settings.project_path.mkdir(parents=True, exist_ok=True)
        (settings.project_path / "chats").mkdir(parents=True, exist_ok=True)
        (settings.project_path / ".aic").mkdir(parents=True, exist_ok=True)
        
        # Set initialization flag
        _project_initialized = True 