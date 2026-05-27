#!/usr/bin/env python3
"""
Configure SC2SC environment variables in Railway

This script:
1. Retrieves CDK deployment outputs
2. Shows you what values to add to Railway
3. Optionally uses Railway CLI to set the variables automatically
"""

import subprocess
import json
import sys
import os

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def run_command(cmd, description=None):
    """Run a command and return output"""
    if description:
        print(f"\n[*] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="sc2sc")
        if result.returncode != 0:
            print(f"[!] Error: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"[!] Error running command: {e}")
        return None

def get_cdk_outputs():
    """Get CDK stack outputs"""
    print("\n" + "="*80)
    print("RETRIEVING CDK STACK OUTPUTS")
    print("="*80)

    # Try to get outputs from CDK
    output = run_command(
        "cdk describe Sc2ScStack --json",
        "Fetching CDK stack information"
    )

    if not output:
        print("\n[!]  Could not get CDK outputs. Trying AWS CLI...")

        # Fall back to AWS CLI
        output = run_command(
            "aws cloudformation describe-stacks --stack-name Sc2ScStack --query 'Stacks[0].Outputs' --output json",
            "Fetching from CloudFormation"
        )

        if not output:
            print("\n[!] Could not retrieve CDK outputs.")
            print("   Make sure you've deployed the CDK stack: 'cdk deploy'")
            return None

    return json.loads(output)

def extract_values(cdk_output):
    """Extract environment variable values from CDK output"""
    print("\n" + "="*80)
    print("EXTRACTED VALUES")
    print("="*80)

    values = {}

    # Parse CDK output (format varies depending on how output is retrieved)
    # CDK outputs are in Metadata.analyticsMetadata format or Outputs array

    if isinstance(cdk_output, dict):
        # Try parsing from describe-stacks JSON
        if 'Outputs' in cdk_output:
            outputs = cdk_output['Outputs']
        elif 'metadata' in cdk_output:
            outputs = cdk_output['metadata']
        else:
            outputs = cdk_output

        # Extract relevant outputs
        for output in (outputs if isinstance(outputs, list) else [outputs]):
            if isinstance(output, dict):
                export_name = output.get('ExportName') or output.get('export_name') or ''
                value = output.get('OutputValue') or output.get('value') or ''

                if 'SNSTopicArn' in export_name or 'SNS' in export_name:
                    values['SNS_TOPIC_ARN'] = value
                elif 'SolQueueUrl' in export_name or 'sol-queue' in value:
                    values['SOL_QUEUE_URL'] = value
                elif 'LexiQueueUrl' in export_name or 'lexi-queue' in value:
                    values['LEXI_QUEUE_URL'] = value

    # These are hardcoded in the CDK stack
    values['CONVERSATIONS_TABLE'] = 'a2a_conversations'
    values['AGENT_REGISTRY_TABLE'] = 'agent_registry'

    # AWS credentials (user must provide)
    values['AWS_REGION'] = 'us-east-1'
    values['AWS_ACCESS_KEY_ID'] = '<your-access-key>'
    values['AWS_SECRET_ACCESS_KEY'] = '<your-secret-key>'

    return values

def show_values(values):
    """Display extracted values"""
    print("\nAdd these variables to your Railway project:\n")

    for key, value in values.items():
        if '<your-' in value:
            print(f"  {key}={value}  ← FILL THIS IN")
        else:
            print(f"  {key}={value}")

def set_railway_variables(values):
    """Attempt to set variables in Railway using CLI"""

    print("\n" + "="*80)
    print("RAILWAY CLI CONFIGURATION")
    print("="*80)

    # Check if railway CLI is installed
    result = subprocess.run("railway --version", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("\n[!]  Railway CLI not installed.")
        print("   Install it: npm install -g railway")
        print("   Then run: railway link")
        print("   Then run: railway variables set KEY=VALUE")
        return False

    print("\nRailway CLI is installed. Attempting to set variables...\n")

    # Try to set each variable
    success_count = 0
    for key, value in values.items():
        if '<your-' not in value:  # Skip placeholder values
            cmd = f"railway variables set {key}={value}"
            print(f"Setting {key}...", end=' ')
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("[OK]")
                success_count += 1
            else:
                print(f"[!] {result.stderr}")

    return success_count > 0

def main():
    print("\n" + "="*80)
    print("SC2SC RAILWAY CONFIGURATION HELPER")
    print("="*80)

    # Check if in correct directory
    if not os.path.exists("sc2sc"):
        print("\n[!] Error: sc2sc directory not found.")
        print("   Run this script from the wootangular369 root directory.")
        sys.exit(1)

    # Get CDK outputs
    print("\n[1]  STEP 1: Get CDK Outputs")
    print("-" * 80)
    print("\nMake sure CDK stack is deployed:")
    print("  cd sc2sc")
    print("  cdk deploy")
    print("\nThen run this script again to extract the outputs.")

    cdk_output = get_cdk_outputs()

    if cdk_output:
        # Extract values
        print("\n[2]  STEP 2: Extract Values")
        values = extract_values(cdk_output)

        # Show values
        show_values(values)

        # Try to set in Railway
        print("\n[3]  STEP 3: Set in Railway")
        print("-" * 80)

        use_cli = input("\nUse Railway CLI to set variables automatically? (y/n): ").strip().lower()

        if use_cli == 'y':
            if set_railway_variables(values):
                print("\n[OK] Variables set successfully!")
                print("\nNow redeploy: git push")
            else:
                print("\n[!]  Some variables may not have been set.")
                print("   Set them manually in Railway dashboard:")
                print("   1. Go to your project")
                print("   2. Select the web service")
                print("   3. Go to Variables tab")
                print("   4. Add each variable from above")
        else:
            print("\n[*] MANUAL SETUP:")
            print("   1. Go to https://railway.app")
            print("   2. Select your project > Sol Calarbone 8 service")
            print("   3. Go to 'Variables' tab")
            print("   4. Add each variable from above")
            print("   5. Redeploy (git push or click Deploy)")
    else:
        print("\n[!] Could not retrieve CDK outputs.")
        print("\nMake sure:")
        print("  1. CDK stack is deployed: 'cdk deploy'")
        print("  2. AWS credentials are configured")
        print("  3. You're in the wootangular369 root directory")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!]  Setup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
