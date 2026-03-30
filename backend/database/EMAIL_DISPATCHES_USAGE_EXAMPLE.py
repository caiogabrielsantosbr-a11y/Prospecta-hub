"""
Example usage of email_dispatches methods in SupabaseClient.

This file demonstrates how the Email Dispatch module would use
the new email_dispatches methods.
"""
import asyncio
from datetime import datetime
from backend.database.supabase_client import get_supabase_client


async def example_email_dispatch_workflow():
    """
    Example workflow showing how to use email_dispatches methods
    in the Email Dispatch module.
    """
    # Get the Supabase client
    client = get_supabase_client()
    
    if not client.is_available():
        print("Supabase integration is not available")
        return
    
    # Example 1: Insert a single email dispatch
    print("\n=== Example 1: Insert Single Dispatch ===")
    dispatch_data = {
        'recipient': 'customer@example.com',
        'subject': 'Welcome to our service!',
        'status': 'pending',
        'task_id': 'email-campaign-001'
    }
    
    success = await client.insert_email_dispatch(dispatch_data)
    if success:
        print(f"✓ Successfully inserted dispatch to {dispatch_data['recipient']}")
    else:
        print(f"✗ Failed to insert dispatch to {dispatch_data['recipient']}")
    
    # Example 2: Batch insert multiple dispatches
    print("\n=== Example 2: Batch Insert Dispatches ===")
    dispatches = [
        {
            'recipient': f'user{i}@example.com',
            'subject': 'Monthly Newsletter',
            'status': 'pending',
            'task_id': 'newsletter-campaign-002'
        }
        for i in range(1, 11)  # 10 dispatches
    ]
    
    success_count, failure_count = await client.insert_email_dispatches_batch(dispatches)
    print(f"✓ Inserted {success_count} dispatches successfully")
    print(f"✗ Failed to insert {failure_count} dispatches")
    
    # Example 3: Query dispatches by task
    print("\n=== Example 3: Query Dispatches by Task ===")
    task_id = 'email-campaign-001'
    dispatches = await client.get_email_dispatches_by_task(task_id, limit=10)
    print(f"Found {len(dispatches)} dispatches for task '{task_id}'")
    
    for dispatch in dispatches[:3]:  # Show first 3
        print(f"  - {dispatch.get('recipient')}: {dispatch.get('status')}")
    
    # Example 4: Update dispatch when email is sent
    print("\n=== Example 4: Update Dispatch After Sending ===")
    # Simulate sending an email and updating the dispatch
    if dispatches:
        dispatch_id = dispatches[0].get('id')
        sent_timestamp = datetime.utcnow().isoformat() + 'Z'
        
        success = await client.update_email_dispatch_sent(dispatch_id, sent_timestamp)
        if success:
            print(f"✓ Updated dispatch {dispatch_id} with sent_at timestamp")
        else:
            print(f"✗ Failed to update dispatch {dispatch_id}")
    
    # Example 5: Pagination for large result sets
    print("\n=== Example 5: Pagination ===")
    task_id = 'newsletter-campaign-002'
    
    # Get first page
    page1 = await client.get_email_dispatches_by_task(task_id, limit=5, offset=0)
    print(f"Page 1: {len(page1)} dispatches")
    
    # Get second page
    page2 = await client.get_email_dispatches_by_task(task_id, limit=5, offset=5)
    print(f"Page 2: {len(page2)} dispatches")


async def example_worker_integration():
    """
    Example showing how the Email Dispatch Worker would use these methods.
    """
    client = get_supabase_client()
    
    if not client.is_available():
        print("Supabase integration is not available")
        return
    
    print("\n=== Email Dispatch Worker Integration Example ===")
    
    # Simulate worker creating dispatches for a campaign
    task_id = 'worker-campaign-003'
    recipients = ['alice@example.com', 'bob@example.com', 'charlie@example.com']
    
    # Step 1: Create dispatch records
    print("\nStep 1: Creating dispatch records...")
    dispatches = [
        {
            'recipient': email,
            'subject': 'Important Update',
            'status': 'pending',
            'task_id': task_id
        }
        for email in recipients
    ]
    
    success_count, failure_count = await client.insert_email_dispatches_batch(dispatches)
    print(f"Created {success_count} dispatch records")
    
    # Step 2: Query pending dispatches
    print("\nStep 2: Querying pending dispatches...")
    pending_dispatches = await client.get_email_dispatches_by_task(task_id)
    print(f"Found {len(pending_dispatches)} pending dispatches")
    
    # Step 3: Simulate sending emails and updating dispatches
    print("\nStep 3: Sending emails and updating dispatches...")
    for dispatch in pending_dispatches:
        dispatch_id = dispatch.get('id')
        recipient = dispatch.get('recipient')
        
        # Simulate email sending
        print(f"  Sending email to {recipient}...")
        
        # Update dispatch with sent timestamp
        sent_timestamp = datetime.utcnow().isoformat() + 'Z'
        success = await client.update_email_dispatch_sent(dispatch_id, sent_timestamp)
        
        if success:
            print(f"  ✓ Marked dispatch {dispatch_id} as sent")
        else:
            print(f"  ✗ Failed to update dispatch {dispatch_id}")
    
    # Step 4: Verify all dispatches were updated
    print("\nStep 4: Verifying dispatch statuses...")
    updated_dispatches = await client.get_email_dispatches_by_task(task_id)
    sent_count = sum(1 for d in updated_dispatches if d.get('status') == 'sent')
    print(f"Total dispatches: {len(updated_dispatches)}")
    print(f"Sent dispatches: {sent_count}")


async def example_error_handling():
    """
    Example showing error handling patterns.
    """
    client = get_supabase_client()
    
    print("\n=== Error Handling Examples ===")
    
    # Example 1: Missing required field
    print("\nExample 1: Missing required field")
    invalid_dispatch = {
        'subject': 'Test Email',
        'status': 'pending'
        # Missing 'recipient' field
    }
    
    success = await client.insert_email_dispatch(invalid_dispatch)
    print(f"Result: {success} (expected False)")
    
    # Example 2: Empty batch
    print("\nExample 2: Empty batch")
    success_count, failure_count = await client.insert_email_dispatches_batch([])
    print(f"Success: {success_count}, Failures: {failure_count} (expected 0, 0)")
    
    # Example 3: Invalid parameters
    print("\nExample 3: Invalid parameters")
    results = await client.get_email_dispatches_by_task('')  # Empty task_id
    print(f"Results: {len(results)} (expected 0)")
    
    # Example 4: Graceful degradation when Supabase unavailable
    print("\nExample 4: Graceful degradation")
    if not client.is_available():
        print("Supabase is unavailable - operations will fail gracefully")
        success = await client.insert_email_dispatch({'recipient': 'test@example.com'})
        print(f"Insert result: {success} (expected False)")


if __name__ == '__main__':
    print("=" * 60)
    print("Email Dispatches Methods Usage Examples")
    print("=" * 60)
    
    # Run examples
    asyncio.run(example_email_dispatch_workflow())
    asyncio.run(example_worker_integration())
    asyncio.run(example_error_handling())
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
