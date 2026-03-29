"""
Base Agent Class
All agents inherit from this base class
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's task
        
        Args:
            context: Shared context dictionary containing data from previous agents
        
        Returns:
            Dict containing the agent's output
        """
        pass
    
    def log_start(self, message: str):
        """Log agent start"""
        self.logger.info(f"[{self.agent_name}] START: {message}")
    
    def log_progress(self, message: str):
        """Log agent progress"""
        self.logger.info(f"[{self.agent_name}] PROGRESS: {message}")
    
    def log_complete(self, message: str):
        """Log agent completion"""
        self.logger.info(f"[{self.agent_name}] COMPLETE: {message}")
    
    def log_error(self, message: str, exc_info: bool = True):
        """Log agent error"""
        self.logger.error(f"[{self.agent_name}] ERROR: {message}", exc_info=exc_info)
