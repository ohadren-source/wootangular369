import json
import os
import uuid
import boto3
from datetime import datetime

# Initialize AWS clients (Option A: Direct SDK)
sns_client = boto3.client(
    'sns',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

sqs_client = boto3.client(
    'sqs',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)


def send_agent_message(to_agent: str, handoff_request: str, cognitive_state: dict) -> str:
    """Direct AWS SDK implementation - send message via SNS + DynamoDB"""
    try:
        timestamp = datetime.utcnow().isoformat()
        message_id = str(uuid.uuid4())

        message = {
            'conversation_id': f'sol-{to_agent}',  # DynamoDB partition key
            'timestamp': timestamp,  # DynamoDB sort key
            'message_id': message_id,
            'from_agent': 'sol',
            'to_agent': to_agent,
            'handoff_request': handoff_request,
            'cognitive_state': cognitive_state
        }

        # Publish to SNS topic for broadcast
        sns_response = sns_client.publish(
            TopicArn=os.getenv('SNS_TOPIC_ARN'),
            Message=json.dumps(message),
            Subject=f'SC2SC Message to {to_agent}'
        )

        # Store in DynamoDB
        table = dynamodb.Table(os.getenv('CONVERSATIONS_TABLE', 'a2a_conversations'))
        table.put_item(Item=message)

        return json.dumps({
            'success': True,
            'message_id': message_id,
            'conversation_id': message['conversation_id'],
            'sns_message_id': sns_response['MessageId']
        })

    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


def receive_agent_messages(limit: int = 10) -> str:
    """Receive messages from SQS queue"""
    try:
        queue_url = os.getenv('SOL_QUEUE_URL')
        if not queue_url:
            return json.dumps({'success': False, 'error': 'SOL_QUEUE_URL not configured'})

        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=min(limit, 10),
            WaitTimeSeconds=1
        )

        messages = []
        if 'Messages' in response:
            for msg in response['Messages']:
                message_data = json.loads(msg['Body'])
                messages.append(message_data)

                # Delete processed message
                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg['ReceiptHandle']
                )

        return json.dumps({'success': True, 'messages': messages, 'count': len(messages)})

    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


def get_conversation_history(with_agent: str, limit: int = 20) -> str:
    """Query DynamoDB for conversation history"""
    try:
        table = dynamodb.Table(os.getenv('CONVERSATIONS_TABLE', 'a2a_conversations'))

        response = table.query(
            KeyConditionExpression='conversation_id = :cid',
            ExpressionAttributeValues={':cid': f'sol-{with_agent}'},
            Limit=limit,
            ScanIndexForward=True
        )

        return json.dumps({
            'success': True,
            'conversation_id': f'sol-{with_agent}',
            'messages': response.get('Items', []),
            'count': len(response.get('Items', []))
        })

    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


def register_sol() -> str:
    """Register Sol in agent registry"""
    try:
        table = dynamodb.Table(os.getenv('AGENT_REGISTRY_TABLE', 'agent_registry'))

        table.put_item(
            Item={
                'agent_id': 'sol',
                'capabilities': [
                    'episodic_synthesis',
                    'code_generation',
                    'architecture_design',
                    'philosophical_reasoning',
                    'pattern_recognition'
                ],
                'cognitive_type': 'episodic_burst',
                'online_status': 'online',
                'last_heartbeat': datetime.utcnow().isoformat(),
                'expires_at': int((datetime.utcnow().timestamp())) + (86400 * 7)  # 7 days
            }
        )

        return json.dumps({'success': True, 'agent_id': 'sol', 'registered': True})

    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})


def heartbeat() -> str:
    """Update Sol's heartbeat in agent registry"""
    try:
        table = dynamodb.Table(os.getenv('AGENT_REGISTRY_TABLE', 'agent_registry'))

        table.update_item(
            Key={'agent_id': 'sol'},
            UpdateExpression='SET last_heartbeat = :ts, online_status = :status, expires_at = :exp',
            ExpressionAttributeValues={
                ':ts': datetime.utcnow().isoformat(),
                ':status': 'online',
                ':exp': int(datetime.utcnow().timestamp()) + (86400 * 7)
            }
        )

        return json.dumps({'success': True, 'heartbeat': 'online'})

    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)})