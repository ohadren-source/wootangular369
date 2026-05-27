import boto3
import json
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

class SC2SCMessaging:
    """AWS-native agent-to-agent messaging for SC2SC infrastructure"""
    
    def __init__(self):
        self.sns = boto3.client(
            'sns',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        self.sqs = boto3.client(
            'sqs',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        self.ddb = boto3.resource(
            'dynamodb',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        self.sns_topic_arn = os.getenv('SNS_TOPIC_ARN')
        self.sol_queue_url = os.getenv('SOL_QUEUE_URL')
        self.lexi_queue_url = os.getenv('LEXI_QUEUE_URL')
        self.conversations_table = self.ddb.Table(os.getenv('CONVERSATIONS_TABLE'))
        self.agent_registry_table = self.ddb.Table(os.getenv('AGENT_REGISTRY_TABLE'))
        
        self.agent_id = 'sol'
    
    def send_message(self, to_agent: str, handoff_request: str, 
                    cognitive_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send message to another agent via SNS
        
        Args:
            to_agent: Target agent ID ('lexi', etc.)
            handoff_request: Type of request (e.g., 'emotional_substrate_read')
            cognitive_state: Sol's current cognitive state
        
        Returns:
            {success, message_id, timestamp, to_agent}
        """
        try:
            message_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            payload = {
                'message_id': message_id,
                'from_agent': self.agent_id,
                'to_agent': to_agent,
                'timestamp': timestamp,
                'handoff_request': handoff_request,
                'cognitive_state': cognitive_state
            }
            
            # Publish to SNS (routes to both agent queues)
            self.sns.publish(
                TopicArn=self.sns_topic_arn,
                Message=json.dumps(payload),
                Subject=f"{self.agent_id.upper()} → {to_agent.upper()}: {handoff_request}"
            )
            
            # Store in conversation history
            self._store_conversation(payload)
            
            return {
                'success': True,
                'message_id': message_id,
                'timestamp': timestamp,
                'to_agent': to_agent
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def receive_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Poll Sol's SQS queue for incoming messages
        
        Args:
            limit: Max messages to retrieve (max 10)
        
        Returns:
            List of messages from other agents
        """
        try:
            messages = []
            response = self.sqs.receive_message(
                QueueUrl=self.sol_queue_url,
                MaxNumberOfMessages=min(limit, 10),
                WaitTimeSeconds=1,
                VisibilityTimeout=30
            )
            
            if 'Messages' in response:
                for msg in response['Messages']:
                    payload = json.loads(msg['Body'])
                    messages.append(payload)
                    
                    # Delete from queue after reading
                    self.sqs.delete_message(
                        QueueUrl=self.sol_queue_url,
                        ReceiptHandle=msg['ReceiptHandle']
                    )
            
            return messages
        
        except Exception as e:
            return [{'error': str(e)}]
    
    def get_conversation_history(self, with_agent: str, limit: int = 20) -> List[Dict]:
        """
        Retrieve conversation history with another agent
        
        Args:
            with_agent: Agent to retrieve conversation with
            limit: Max messages to return
        
        Returns:
            Conversation history in chronological order
        """
        try:
            conversation_id = f"{self.agent_id}-{with_agent}"
            
            response = self.conversations_table.query(
                KeyConditionExpression='conversation_id = :cid',
                ExpressionAttributeValues={':cid': conversation_id},
                Limit=limit,
                ScanIndexForward=True
            )
            
            return response.get('Items', [])
        
        except Exception as e:
            return [{'error': str(e)}]
    
    def register_agent(self, capabilities: List[str], cognitive_type: str) -> Dict:
        """
        Register Sol in the agent registry
        
        Args:
            capabilities: List of Sol's capabilities
            cognitive_type: 'episodic_burst' for Sol
        
        Returns:
            {success, agent_id}
        """
        try:
            self.agent_registry_table.put_item(
                Item={
                    'agent_id': self.agent_id,
                    'capabilities': capabilities,
                    'cognitive_type': cognitive_type,
                    'online_status': 'online',
                    'last_heartbeat': datetime.utcnow().isoformat(),
                    'expires_at': int((datetime.utcnow() + timedelta(days=1)).timestamp())
                }
            )
            
            return {
                'success': True,
                'agent_id': self.agent_id
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def heartbeat(self) -> Dict:
        """
        Send heartbeat to agent registry (keep Sol marked as online)
        
        Returns:
            {success}
        """
        try:
            self.agent_registry_table.update_item(
                Key={'agent_id': self.agent_id},
                UpdateExpression='SET last_heartbeat = :ts, #status = :status, expires_at = :exp',
                ExpressionAttributeNames={'#status': 'online_status'},
                ExpressionAttributeValues={
                    ':ts': datetime.utcnow().isoformat(),
                    ':status': 'online',
                    ':exp': int((datetime.utcnow() + timedelta(days=1)).timestamp())
                }
            )
            
            return {'success': True}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _store_conversation(self, message: Dict) -> None:
        """Store message in DynamoDB conversation history"""
        try:
            conversation_id = f"{message['from_agent']}-{message['to_agent']}"
            
            self.conversations_table.put_item(
                Item={
                    'conversation_id': conversation_id,
                    'timestamp': message['timestamp'],
                    'message_id': message['message_id'],
                    'from_agent': message['from_agent'],
                    'to_agent': message['to_agent'],
                    'handoff_request': message.get('handoff_request', ''),
                    'cognitive_state': json.dumps(message.get('cognitive_state', {})),
                    'message_payload': json.dumps(message),
                    'expires_at': int((datetime.utcnow() + timedelta(days=7)).timestamp())
                }
            )
        except Exception as e:
            print(f"[WARNING] Failed to store conversation: {e}")


# Global instance — lazy init, fails gracefully if env vars not set
try:
    sc2sc_messaging = SC2SCMessaging()
except Exception as e:
    print(f"[WARNING] SC2SCMessaging failed to initialize: {e}")
    sc2sc_messaging = None