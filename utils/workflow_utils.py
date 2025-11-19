from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import time
import json
import os

class WorkflowStatus(Enum):
    """Workflow status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"

class StepStatus(Enum):
    """Individual step status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"

class WorkflowState:
    """Manages the state of the entire workflow"""
    
    def __init__(self):
        self.workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = None
        self.end_time = None
        self.status = WorkflowStatus.PENDING
        self.steps = {}
        self.results = {}
        self.errors = []
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "total_steps": 0,
            "completed_steps": 0,
            "failed_steps": 0,
        }
    
    def start_workflow(self):
        """Mark workflow as started"""
        self.start_time = datetime.now()
        self.status = WorkflowStatus.RUNNING
    
    def complete_workflow(self, status: WorkflowStatus = WorkflowStatus.SUCCESS):
        """Mark workflow as completed"""
        self.end_time = datetime.now()
        self.status = status
        self.metadata["completed_at"] = self.end_time.isoformat()
        self.metadata["duration_seconds"] = (self.end_time - self.start_time).total_seconds()
    
    def add_step(self, step_name: str, description: str = ""):
        """Add a step to the workflow"""
        self.steps[step_name] = {
            "name": step_name,
            "description": description,
            "status": StepStatus.PENDING,
            "attempts": 0,
            "max_attempts": 3,
            "start_time": None,
            "end_time": None,
            "duration": None,
            "error": None,
            "result": None,
        }
        self.metadata["total_steps"] += 1
    
    def start_step(self, step_name: str, attempt: int = 1):
        """Mark step as started"""
        if step_name in self.steps:
            self.steps[step_name]["status"] = StepStatus.RUNNING
            self.steps[step_name]["attempts"] = attempt
            self.steps[step_name]["start_time"] = datetime.now()
    
    def complete_step(self, step_name: str, result: Any = None, error: str = None):
        """Mark step as completed"""
        if step_name in self.steps:
            step = self.steps[step_name]
            step["end_time"] = datetime.now()
            
            if step["start_time"]:
                step["duration"] = (step["end_time"] - step["start_time"]).total_seconds()
            
            if error:
                step["status"] = StepStatus.FAILED
                step["error"] = error
                self.metadata["failed_steps"] += 1
                self.errors.append({
                    "step": step_name,
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                step["status"] = StepStatus.SUCCESS
                step["result"] = result
                self.results[step_name] = result
                self.metadata["completed_steps"] += 1
    
    def retry_step(self, step_name: str):
        """Mark step for retry"""
        if step_name in self.steps:
            self.steps[step_name]["status"] = StepStatus.RETRYING
    
    def skip_step(self, step_name: str, reason: str = ""):
        """Mark step as skipped"""
        if step_name in self.steps:
            self.steps[step_name]["status"] = StepStatus.SKIPPED
            self.steps[step_name]["error"] = reason
    
    def get_step_status(self, step_name: str) -> Optional[StepStatus]:
        """Get status of a specific step"""
        if step_name in self.steps:
            return self.steps[step_name]["status"]
        return None
    
    def get_step_result(self, step_name: str) -> Optional[Any]:
        """Get result of a specific step"""
        return self.results.get(step_name)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get workflow summary"""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.metadata.get("duration_seconds"),
            "total_steps": self.metadata["total_steps"],
            "completed_steps": self.metadata["completed_steps"],
            "failed_steps": self.metadata["failed_steps"],
            "success_rate": (self.metadata["completed_steps"] / self.metadata["total_steps"] * 100) if self.metadata["total_steps"] > 0 else 0,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow state to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "metadata": self.metadata,
            "steps": {
                name: {
                    **step,
                    "status": step["status"].value if isinstance(step["status"], StepStatus) else step["status"],
                    "start_time": step["start_time"].isoformat() if step["start_time"] else None,
                    "end_time": step["end_time"].isoformat() if step["end_time"] else None,
                }
                for name, step in self.steps.items()
            },
            "errors": self.errors,
        }
    
    def save_to_file(self, directory: str = "output/logs"):
        """Save workflow state to file"""
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f"{self.workflow_id}_state.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        
        return filepath

class RetryHelper:
    """Helper for implementing retry logic"""
    
    @staticmethod
    def should_retry(attempt: int, max_attempts: int, error: Exception) -> bool:
        """Determine if operation should be retried"""
        if attempt >= max_attempts:
            return False
        
        # Don't retry certain types of errors
        non_retriable_errors = [
            "authentication",
            "authorization",
            "invalid_api_key",
        ]
        
        error_str = str(error).lower()
        if any(err in error_str for err in non_retriable_errors):
            return False
        
        return True
    
    @staticmethod
    def get_delay(attempt: int, base_delay: int = 5) -> float:
        """Calculate delay before next retry (exponential backoff)"""
        return base_delay * (2 ** (attempt - 1))
    
    @staticmethod
    def wait_before_retry(attempt: int, base_delay: int = 5):
        """Wait before retrying"""
        delay = RetryHelper.get_delay(attempt, base_delay)
        print(f"   ⏳ Waiting {delay} seconds before retry...")
        time.sleep(delay)

def format_workflow_report(state: WorkflowState) -> str:
    """Format workflow state into a readable report"""
    
    summary = state.get_summary()
    
    report = f"""
# Workflow Execution Report
**Workflow ID:** {summary['workflow_id']}
**Status:** {summary['status'].upper()}

## ⏱️ Timing
- **Started:** {summary['start_time']}
- **Ended:** {summary['end_time'] or 'In Progress'}
- **Duration:** {summary['duration']:.2f} seconds ({summary['duration']/60:.1f} minutes)

## 📊 Summary
- **Total Steps:** {summary['total_steps']}
- **Completed:** {summary['completed_steps']} ✅
- **Failed:** {summary['failed_steps']} ❌
- **Success Rate:** {summary['success_rate']:.1f}%

## 📋 Step Details

"""
    
    # Add details for each step
    for step_name, step in state.steps.items():
        status_emoji = {
            StepStatus.SUCCESS: "✅",
            StepStatus.FAILED: "❌",
            StepStatus.RUNNING: "🔄",
            StepStatus.PENDING: "⏸️",
            StepStatus.RETRYING: "🔁",
            StepStatus.SKIPPED: "⏭️",
        }.get(step["status"], "❓")
        
        report += f"""### {status_emoji} {step_name.replace('_', ' ').title()}
- **Status:** {step['status'].value}
- **Attempts:** {step['attempts']}/{step['max_attempts']}

"""
        
        if step['error']:
            report += f"- **Error:** {step['error']}\n"
        
        report += "\n"
    
    # Add errors section if any
    if state.errors:
        report += "\n## ⚠️ Errors Encountered\n\n"
        for i, error in enumerate(state.errors, 1):
            report += f"{i}. **{error['step']}:** {error['error']}\n"
    
    return report

def log_workflow_step(step_name: str, message: str, level: str = "INFO"):
    """Log a workflow step message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    emoji = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "DEBUG": "🔍",
    }.get(level, "📝")
    
    print(f"[{timestamp}] {emoji} [{step_name}] {message}")