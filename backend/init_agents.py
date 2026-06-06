"""
Initialize and register all specialized agents with the agent orchestrator.
This script should be called during application startup.
"""
import logging
from backend.agent_orchestrator import get_orchestrator
from backend.fomc_agent import FOMCAgent
from backend.speech_agent import SpeechAgent
from backend.news_agent import NewsAgent
from backend.market_agent import MarketAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_agents():
    """Initialize and register all agents with the orchestrator."""
    logger.info("Initializing Multi-Agent Intelligence System...")
    
    orchestrator = get_orchestrator()
    
    # Register FOMC Agent
    fomc_agent = FOMCAgent()
    orchestrator.register_agent(fomc_agent)
    
    # Register Speech Agent
    speech_agent = SpeechAgent()
    orchestrator.register_agent(speech_agent)
    
    # Register News Agent
    news_agent = NewsAgent()
    orchestrator.register_agent(news_agent)
    
    # Register Market Agent
    market_agent = MarketAgent()
    orchestrator.register_agent(market_agent)
    
    logger.info(f"Successfully initialized {len(orchestrator.agents)} agents")
    
    # Log agent capabilities
    for agent_info in orchestrator.list_agents():
        logger.info(f"Agent: {agent_info['name']} - {agent_info['description']}")
        logger.info(f"  Capabilities: {', '.join(agent_info['capabilities'])}")
    
    return orchestrator

if __name__ == "__main__":
    initialize_agents()
