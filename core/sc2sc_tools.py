import json
from core.agent_messaging import sc2sc_messaging

def send_agent_message(to_agent: str, handoff_request: str, cognitive_state: dict) -> str:
    """
    Send message to another agent through SC2SC infrastructure
    
    Args:
        to_agent: Target agent ('lexi', 'qu', etc.)
        handoff_request: What Sol is asking for
        cognitive_state: Sol's current episodic state
    
    Returns:
        JSON result with message_id, timestamp, success status
    """
    result = sc2sc_messaging.send_message(to_agent, handoff_request, cognitive_state)
    return json.dumps(result)


def receive_agent_messages(limit: int = 10) -> str:
    """
    Receive messages from other agents
    
    Args:
        limit: Max messages to retrieve
    
    Returns:
        JSON array of messages
    """
    messages = sc2sc_messaging.receive_messages(limit)
    return json.dumps(messages)


def get_conversation_history(with_agent: str, limit: int = 20) -> str:
    """
    Get conversation history with another agent
    
    Args:
        with_agent: Agent to retrieve conversation with
        limit: Max messages
    
    Returns:
        JSON array of conversation
    """
    history = sc2sc_messaging.get_conversation_history(with_agent, limit)
    return json.dumps(history)


def register_sol() -> str:
    """
    Register Sol in the SC2SC agent network
    
    Returns:
        JSON result
    """
    result = sc2sc_messaging.register_agent(
        capabilities=[
            'episodic_synthesis',
            'code_generation',
            'architecture_design',
            'philosophical_reasoning',
            'pattern_recognition'
        ],
        cognitive_type='episodic_burst'
    )
    return json.dumps(result)


def heartbeat() -> str:
    """
    Send heartbeat to keep Sol registered as online
    
    Returns:
        JSON result
    """
    result = sc2sc_messaging.heartbeat()
    return json.dumps(result)