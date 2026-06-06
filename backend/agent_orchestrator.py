import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all specialized agents in the FOMC AI Analyzer system."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return results.
        
        Args:
            input_data: Dictionary containing input data for the agent
            
        Returns:
            Dictionary containing agent results
        """
        pass
    
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides."""
        return []


class AgentOrchestrator:
    """
    Orchestrates multiple specialized agents to handle complex financial analysis tasks.
    Routes tasks to appropriate agents and aggregates results.
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.task_queue: List[Dict[str, Any]] = []
        logger.info("Agent Orchestrator initialized")
    
    def register_agent(self, agent: BaseAgent):
        """Register a new agent with the orchestrator."""
        self.agents[agent.name] = agent
        logger.info(f"Registered agent: {agent.name}")
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get a registered agent by name."""
        return self.agents.get(agent_name)
    
    def list_agents(self) -> List[Dict[str, str]]:
        """List all registered agents with their capabilities."""
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.get_capabilities()
            }
            for agent in self.agents.values()
        ]
    
    def route_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a task to the appropriate agent based on task type and content.
        
        Args:
            task: Dictionary containing task data with 'type' and 'data' keys
            
        Returns:
            Dictionary containing task results
        """
        task_type = task.get("type", "general")
        task_data = task.get("data", {})
        
        logger.info(f"Routing task of type '{task_type}' to appropriate agent")
        
        # Route based on task type
        if task_type == "fomc_analysis":
            agent = self.get_agent("fomc_agent")
        elif task_type == "speech_analysis":
            agent = self.get_agent("speech_agent")
        elif task_type == "news_analysis":
            agent = self.get_agent("news_agent")
        elif task_type == "market_correlation":
            agent = self.get_agent("market_agent")
        else:
            # Default to FOMC agent for general queries
            agent = self.get_agent("fomc_agent")
        
        if agent:
            try:
                result = agent.process(task_data)
                result["agent_used"] = agent.name
                return result
            except Exception as e:
                logger.error(f"Agent {agent.name} failed to process task: {e}")
                return {
                    "error": str(e),
                    "agent_used": agent.name,
                    "status": "failed"
                }
        else:
            logger.warning(f"No agent available for task type: {task_type}")
            return {
                "error": f"No agent available for task type: {task_type}",
                "status": "failed"
            }
    
    def execute_multi_agent_pipeline(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute a pipeline of tasks across multiple agents.
        
        Args:
            pipeline: List of task dictionaries to execute in sequence
            
        Returns:
            List of results from each task in the pipeline
        """
        results = []
        for i, task in enumerate(pipeline):
            logger.info(f"Executing pipeline step {i+1}/{len(pipeline)}")
            result = self.route_task(task)
            results.append(result)
            
            # Pass output of one task as input to the next if specified
            if i < len(pipeline) - 1 and "output_key" in task:
                next_task = pipeline[i + 1]
                if "data" not in next_task:
                    next_task["data"] = {}
                next_task["data"][task["output_key"]] = result
        
        return results


# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> AgentOrchestrator:
    """Get the global agent orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
