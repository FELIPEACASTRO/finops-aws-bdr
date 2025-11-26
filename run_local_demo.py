#!/usr/bin/env python3
"""
Local demo runner for FinOps AWS
Simulates Lambda execution environment for local testing
"""
import json
import sys
import os
from datetime import datetime

# Set up Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_banner():
    """Print welcome banner"""
    print("=" * 80)
    print("FinOps AWS - Local Demo Runner")
    print("=" * 80)
    print()
    print("This is a simulation environment for testing the AWS Lambda function locally.")
    print("Note: Actual AWS API calls require valid AWS credentials and permissions.")
    print()
    print("=" * 80)
    print()

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    has_credentials = (
        os.getenv('AWS_ACCESS_KEY_ID') or 
        os.getenv('AWS_PROFILE') or
        os.path.exists(os.path.expanduser('~/.aws/credentials'))
    )
    
    if has_credentials:
        print("✓ AWS credentials detected")
        return True
    else:
        print("⚠ No AWS credentials detected")
        print("  The demo will use mocked AWS services (moto library)")
        print("  To use real AWS services, configure AWS credentials:")
        print("    - Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("    - Or configure ~/.aws/credentials")
        print()
        return False

def run_with_mocked_services():
    """Run with mocked AWS services for demonstration"""
    print("Running in DEMO MODE with mocked AWS services...")
    print()
    
    from moto import mock_aws
    
    # Mock AWS services
    with mock_aws():
        # Set up minimal mock environment
        import boto3
        
        # Create mock S3 bucket for state management
        s3_client = boto3.client('s3', region_name='us-east-1')
        try:
            s3_client.create_bucket(Bucket='finops-demo-state')
            print("✓ Created mock S3 bucket for state management")
        except Exception as e:
            print(f"  Note: {e}")
        
        # Import and run the handler
        try:
            from finops_aws.lambda_handler import lambda_handler
            
            # Create mock event and context
            class MockContext:
                aws_request_id = 'demo-local-request-123'
                function_name = 'finops-aws-demo'
                invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:finops-aws-demo'
                memory_limit_in_mb = '1024'
                
            event = {
                'source': 'demo.local',
                'detail-type': 'Manual Execution',
                'time': datetime.now().isoformat()
            }
            
            print("=" * 80)
            print("Executing Lambda Handler...")
            print("=" * 80)
            print()
            
            result = lambda_handler(event, MockContext())
            
            print()
            print("=" * 80)
            print("Execution Result:")
            print("=" * 80)
            print()
            print(f"Status Code: {result.get('statusCode')}")
            print()
            
            if result.get('statusCode') == 200:
                print("✓ Execution completed successfully!")
                print()
                body = json.loads(result.get('body', '{}'))
                
                # Print summary if available
                if 'summary' in body:
                    print("Summary:")
                    print(json.dumps(body['summary'], indent=2, default=str))
            else:
                print("✗ Execution failed")
                print(result.get('body', 'No error details available'))
                
            return result
            
        except ImportError as e:
            print(f"✗ Import Error: {e}")
            print()
            print("The Lambda handler could not be imported.")
            print("This is expected in a demo environment without full AWS setup.")
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
        except Exception as e:
            print(f"✗ Execution Error: {e}")
            print()
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {str(e)}")
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

def run_tests():
    """Run the test suite"""
    print()
    print("=" * 80)
    print("Running Test Suite...")
    print("=" * 80)
    print()
    
    import pytest
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        'tests/',
        '-v',
        '--tb=short',
        '-W', 'ignore::DeprecationWarning'
    ])
    
    print()
    if exit_code == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ Tests failed with exit code: {exit_code}")
    
    return exit_code

def main():
    """Main entry point"""
    print_banner()
    
    # Check for AWS credentials
    has_credentials = check_aws_credentials()
    print()
    
    # Show menu
    print("Choose an option:")
    print("  1. Run Lambda handler demo (with mocked AWS services)")
    print("  2. Run test suite")
    print("  3. Run both")
    print()
    
    # Auto-select option 1 for automated runs
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Enter your choice (1-3) [default: 1]: ").strip() or "1"
    
    print()
    
    if choice == "1":
        run_with_mocked_services()
    elif choice == "2":
        run_tests()
    elif choice == "3":
        run_with_mocked_services()
        run_tests()
    else:
        print(f"Invalid choice: {choice}")
        return 1
    
    print()
    print("=" * 80)
    print("Demo completed!")
    print()
    print("For production deployment to AWS Lambda:")
    print("  - Review infrastructure/cloudformation-template.yaml")
    print("  - Use deploy.sh script to deploy to AWS")
    print("  - See README.md for detailed deployment instructions")
    print("=" * 80)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
