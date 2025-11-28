import json
import sys
from typing import List, Dict, Any, Optional
class JSONOutput:
    """Handles JSON output formatting for Zenco CLI."""
    
    def __init__(self, version: str = "1.2.0"):
        self.version = version
        self.results: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
    
    def add_file_result(
        self,
        filepath: str,
        language: str,
        success: bool,
        original_content: str,
        modified_content: str,
        changes: List[Dict[str, Any]],
        stats: Dict[str, int],
        error: Optional[str] = None
    ):
        """Add a file processing result."""
        result = {
            "file": filepath,
            "language": language,
            "success": success,
            "original_content": original_content,
            "modified_content": modified_content,
            "changes": changes,
            "stats": stats
        }
        if error:
            result["error"] = error
        
        self.results.append(result)
    
    def add_error(self, error_type: str, message: str, file: Optional[str] = None):
        """Add a global error."""
        error = {
            "type": error_type,
            "message": message
        }
        if file:
            error["file"] = file
        
        self.errors.append(error)
    
    def output(self, mode: str, in_place: bool):
        """Output the final JSON to stdout."""
        output = {
            "success": len(self.errors) == 0,
            "version": self.version,
            "files_processed": len(self.results),
            "mode": "apply" if in_place else "preview",
            "results": self.results
        }
        
        if self.errors:
            output["errors"] = self.errors
        
        # Print to stdout (VS Code extension will capture this)
        print(json.dumps(output, indent=2))