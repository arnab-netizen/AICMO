"""Project management system interface.

Stage PM: Project & Resource Management
Abstract interface for project management tools and resource planning systems.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import date

from aicmo.pm.domain import (
    Task,
    Resource,
    ResourceAllocation,
    TaskStatus,
)


class ProjectManagementSystem(ABC):
    """
    Abstract interface for project management systems.
    
    Stage PM: Skeleton interface - implement concrete adapters for:
    - Asana (task management)
    - Monday.com (project management)
    - Jira (issue tracking)
    - ClickUp (project management)
    - Trello (kanban boards)
    - Microsoft Project (enterprise PM)
    - Smartsheet (work management)
    - Float (resource planning)
    - Forecast (resource management)
    - etc.
    
    Future: Add real PM system integration here.
    """
    
    @abstractmethod
    def create_task(
        self,
        task: Task
    ) -> str:
        """
        Create a new task in the PM system.
        
        Args:
            task: Task details
            
        Returns:
            Task ID
            
        Raises:
            NotImplementedError: Stage PM skeleton
        """
        raise NotImplementedError("Stage PM: PM system integration pending")
    
    @abstractmethod
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus
    ) -> bool:
        """
        Update task status.
        
        Args:
            task_id: Task ID
            status: New status
            
        Returns:
            True if updated successfully
            
        Raises:
            NotImplementedError: Stage PM skeleton
        """
        raise NotImplementedError("Stage PM: Task update integration pending")
    
    @abstractmethod
    def get_project_tasks(
        self,
        project_id: str,
        status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """
        Get tasks for a project.
        
        Args:
            project_id: Project ID
            status: Optional status filter
            
        Returns:
            List of tasks
            
        Raises:
            NotImplementedError: Stage PM skeleton
        """
        raise NotImplementedError("Stage PM: Task query integration pending")
    
    @abstractmethod
    def allocate_resource(
        self,
        allocation: ResourceAllocation
    ) -> str:
        """
        Allocate a resource to a project.
        
        Args:
            allocation: Resource allocation details
            
        Returns:
            Allocation ID
            
        Raises:
            NotImplementedError: Stage PM skeleton
        """
        raise NotImplementedError("Stage PM: Resource allocation integration pending")
    
    @abstractmethod
    def get_resource_availability(
        self,
        resource_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, float]:
        """
        Get resource availability for date range.
        
        Args:
            resource_id: Resource ID
            start_date: Start date
            end_date: End date
            
        Returns:
            Dict with availability metrics
            
        Raises:
            NotImplementedError: Stage PM skeleton
        """
        raise NotImplementedError("Stage PM: Availability check integration pending")
    
    @abstractmethod
    def sync_project_data(
        self,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Sync project data from PM system.
        
        Args:
            project_id: Project ID
            
        Returns:
            Updated project data
            
        Raises:
            NotImplementedError: Stage PM skeleton
        """
        raise NotImplementedError("Stage PM: Data sync integration pending")
