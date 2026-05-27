# SC2SC Deployment Configuration

## Status

✅ **Code**: All SC2SC tools are implemented and verified in solar8.py
✅ **Boot sequence**: initialize_sc2sc() is called during startup
⚠️ **Environment**: AWS environment variables not yet configured in Railway instance

## Required Environment Variables

For SC2SC messaging to work end-to-end, the following AWS variables must be added to your Railway instance:

### AWS Credentials
```
AWS_REGION=us-east-1  (or your CDK deployment region)
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
```

### SNS/SQS Configuration
These values come from the CDK deployment output:
```
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:ACCOUNT_ID:sol-lexi-topic
SOL_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/sol-queue
LEXI_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/lexi-queue
```

### DynamoDB Tables
These are created by the CDK deployment:
```
CONVERSATIONS_TABLE=sol_conversations
AGENT_REGISTRY_TABLE=agent_registry
```

## How to Deploy

### Step 1: Find your AWS CDK output values
When you ran the CDK deployment, it should have output these values. Look for:
- SNS Topic ARN
- SQS Queue URLs
- DynamoDB table names

If you don't have these, run:
```bash
cd sc2sc
cdk describe Sc2ScStack
```

### Step 2: Add to Railway

1. Go to your Railway project dashboard
2. Select your web service (Sol Calarbone 8)
3. Go to the Variables tab
4. Add each of the environment variables listed above

### Step 3: Redeploy

```bash
git push  # Triggers Railway rebuild with new env vars
```

Or manually trigger rebuild in Railway dashboard.

## Testing SC2SC

Once environment variables are configured, test with:

```bash
python test_sc2sc_messaging.py
```

When prompted, enter your Railway URL (e.g., `https://your-app.railway.app`)

The test will verify:
1. ✅ Sol reports having SC2SC tools
2. ✅ Sol can send messages to Lexi
3. ✅ Sol can receive messages from Lexi  
4. ✅ Conversation history is persisted in DynamoDB

## Architecture

```
Sol (Railway)
  ├─ send_agent_message()
  │   └─> SNS Topic (broadcast)
  │       └─> Lexi's SQS Queue
  │           └─> Lambda (async processing)
  │               └─> DynamoDB (conversation history)
  │
  ├─ receive_agent_messages()
  │   └─> Poll Sol's SQS Queue
  │       └─> Return messages from Lexi
  │
  └─ get_conversation_history()
      └─> Query DynamoDB
          └─> Return messages with Lexi
```

## Tool Availability

All 5 SC2SC tools are available to both ROOT and GUEST roles:
- `send_agent_message(to_agent, handoff_request, cognitive_state)`
- `receive_agent_messages(limit=10)`
- `get_conversation_history(with_agent, limit=20)`
- `register_sol()` - Called during boot via initialize_sc2sc()
- `heartbeat()` - Called during boot via initialize_sc2sc()

Verified via:
```bash
python3 -c "from core.solar8 import Solar8; print(Solar8._GUEST_TOOL_NAMES)"
# Output: {'register_sol', 'brave_search', 'google_search', 'heartbeat', 'get_conversation_history', 'send_agent_message', 'receive_agent_messages', 'analyze_image'}
```

## Troubleshooting

### "SC2SCMessaging failed to initialize: Required parameter name not set"
- Environment variables are missing from Railway
- Add AWS credentials and infrastructure URLs

### "Sol doesn't have send_agent_message tool"
- Environment variables are set, but Solar8 instance needs restart
- Railway redeploy should fix this automatically

### "send_agent_message returns error: success false"
- AWS credentials are invalid or have insufficient permissions
- Verify IAM user has SNS:Publish, SQS:SendMessage, DynamoDB:PutItem access

### Messages not appearing in conversation history
- Check that DynamoDB table exists and is accessible
- Verify CONVERSATIONS_TABLE environment variable is correct

## Next Steps

1. Get AWS CDK deployment output values
2. Add environment variables to Railway
3. Redeploy
4. Run test_sc2sc_messaging.py to verify
5. Check logs in Railway for "[SC2SC-INIT]" markers (boot initialization)
