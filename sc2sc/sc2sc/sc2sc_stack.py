from aws_cdk import (
    aws_sns as sns,
    aws_sqs as sqs,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_kms as kms,
    aws_iam as iam,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
)
from aws_cdk.aws_sns_subscriptions import SqsSubscription
from constructs import Construct


class Sc2ScStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ========== KMS KEY ==========
        kms_key = kms.Key(self, "CognitiveStateEncryption",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY
        )

        # ========== SNS TOPIC (Standard - High Throughput) ==========
        messaging_topic = sns.Topic(self, "AgentMessagingRelay",
            display_name="SC2SC Agent Messaging",
            fifo=False
        )

        # ========== SQS QUEUES (Per Agent) ==========
        sol_dlq = sqs.Queue(self, "SolQueueDLQ", 
            queue_name="sol-queue-dlq"
        )

        sol_queue = sqs.Queue(self, "SolQueue",
            queue_name="sol-queue",
            visibility_timeout=Duration.seconds(30),
            retention_period=Duration.days(7),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=sol_dlq
            )
        )

        lexi_dlq = sqs.Queue(self, "LexiQueueDLQ", 
            queue_name="lexi-queue-dlq"
        )

        lexi_queue = sqs.Queue(self, "LexiQueue",
            queue_name="lexi-queue",
            visibility_timeout=Duration.seconds(30),
            retention_period=Duration.days(7),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=lexi_dlq
            )
        )

        # Subscribe queues to SNS topic
        messaging_topic.add_subscription(SqsSubscription(sol_queue))
        messaging_topic.add_subscription(SqsSubscription(lexi_queue))

        # ========== DYNAMODB TABLES ==========
        
        conversations_table = dynamodb.Table(self, "A2AConversations",
            table_name="a2a_conversations",
            partition_key=dynamodb.Attribute(name="conversation_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="expires_at",
            removal_policy=RemovalPolicy.DESTROY
        )

        conversations_table.add_global_secondary_index(
            index_name="from_agent-timestamp-index",
            partition_key=dynamodb.Attribute(name="from_agent", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL
        )

        conversations_table.add_global_secondary_index(
            index_name="to_agent-timestamp-index",
            partition_key=dynamodb.Attribute(name="to_agent", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL
        )

        agent_registry = dynamodb.Table(self, "AgentRegistry",
            table_name="agent_registry",
            partition_key=dynamodb.Attribute(name="agent_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="expires_at",
            removal_policy=RemovalPolicy.DESTROY
        )

        # ========== S3 BUCKET ==========
        account_id = Stack.of(self).account
        context_bucket = s3.Bucket(self, "AgentContextStorage",
            bucket_name=f"sc2sc-context-storage-{account_id}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY
        )

        context_bucket.add_lifecycle_rule(
            abort_incomplete_multipart_upload_after=Duration.days(7)
        )

        # ========== LAMBDA ROLE ==========
        lambda_role = iam.Role(self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        messaging_topic.grant_publish(lambda_role)
        sol_queue.grant_send_messages(lambda_role)
        lexi_queue.grant_send_messages(lambda_role)
        conversations_table.grant_read_write_data(lambda_role)
        agent_registry.grant_read_write_data(lambda_role)
        context_bucket.grant_read_write(lambda_role)
        kms_key.grant_encrypt_decrypt(lambda_role)

        # ========== CLOUDWATCH LOG GROUPS ==========
        process_logs = logs.LogGroup(self, "ProcessMessageLogs",
            log_group_name="/aws/lambda/process_agent_message",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        health_logs = logs.LogGroup(self, "HealthMonitorLogs",
            log_group_name="/aws/lambda/agent_health_monitor",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        # ========== LAMBDA: Process Agent Message ==========
        process_message_function = lambda_.Function(self, "ProcessAgentMessage",
            function_name="process_agent_message",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import json
import boto3
from datetime import datetime

ddb = boto3.resource('dynamodb')

def handler(event, context):
    try:
        for record in event.get('Records', []):
            message = json.loads(record['Sns']['Message'])
            
            table = ddb.Table('a2a_conversations')
            table.put_item(
                Item={
                    'conversation_id': f"{message['from_agent']}-{message['to_agent']}",
                    'timestamp': message['timestamp'],
                    'message_id': message['message_id'],
                    'from_agent': message['from_agent'],
                    'to_agent': message['to_agent'],
                    'message_payload': json.dumps(message),
                    'expires_at': int(datetime.utcnow().timestamp()) + (7 * 24 * 3600)
                }
            )
            
        return {'statusCode': 200, 'body': 'OK'}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}
            """),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            log_group=process_logs
        )

        # ========== LAMBDA: Agent Health Monitor ==========
        health_monitor_function = lambda_.Function(self, "AgentHealthMonitor",
            function_name="agent_health_monitor",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import boto3
from datetime import datetime, timedelta

ddb = boto3.resource('dynamodb')

def handler(event, context):
    try:
        table = ddb.Table('agent_registry')
        response = table.scan()
        
        for item in response.get('Items', []):
            last_heartbeat = item.get('last_heartbeat')
            if last_heartbeat:
                try:
                    last_beat = datetime.fromisoformat(last_heartbeat)
                    if datetime.utcnow() - last_beat > timedelta(minutes=5):
                        item['online_status'] = 'offline'
                        table.put_item(Item=item)
                except:
                    pass
        
        return {'statusCode': 200, 'body': 'OK'}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}
            """),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=128,
            log_group=health_logs
        )

        # ========== CLOUDWATCH EVENT ==========
        health_check_rule = events.Rule(self, "HealthCheckRule",
            schedule=events.Schedule.rate(Duration.minutes(1))
        )
        health_check_rule.add_target(targets.LambdaFunction(health_monitor_function))

        # ========== OUTPUTS ==========
        CfnOutput(self, "SNSTopicArn",
            value=messaging_topic.topic_arn,
            export_name="SC2SC-SNSTopicArn"
        )

        CfnOutput(self, "SolQueueUrl",
            value=sol_queue.queue_url,
            export_name="SC2SC-SolQueueUrl"
        )

        CfnOutput(self, "LexiQueueUrl",
            value=lexi_queue.queue_url,
            export_name="SC2SC-LexiQueueUrl"
        )

        CfnOutput(self, "ConversationsTableName",
            value=conversations_table.table_name,
            export_name="SC2SC-ConversationsTableName"
        )

        CfnOutput(self, "AgentRegistryTableName",
            value=agent_registry.table_name,
            export_name="SC2SC-AgentRegistryTableName"
        )

        CfnOutput(self, "ContextBucketName",
            value=context_bucket.bucket_name,
            export_name="SC2SC-ContextBucketName"
        )

        CfnOutput(self, "KMSKeyId",
            value=kms_key.key_id,
            export_name="SC2SC-KMSKeyId"
        )