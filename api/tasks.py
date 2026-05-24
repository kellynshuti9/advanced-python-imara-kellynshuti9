from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
import logging
import traceback

# Set up logger
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_alert(self, financing_id):
    """
    Send alert asynchronously when financing request is created or updated.
    
    Args:
        financing_id (int): ID of the FinancingRequest instance
    
    Returns:
        str: Status message
    
    Logs:
        - Success: 'Alert processed for financing request {id}'
        - Failure: Error details with retry info
    """
    
    try:
        # Simulate external alert dispatch (e.g., SMS, email, webhook)
        # In production, replace with actual API call to alert provider
        
        # Remove time.sleep(5) - it's not production-shaped!
        # Instead, we'll just log immediately
        
        with open('alerts.log', 'a') as file:
            file.write(
                f"Alert processed for financing request {financing_id}\n"
            )
        
        logger.info(f"Alert sent successfully for financing request {financing_id}")
        return f"Alert sent for financing request {financing_id}"
    
    except FileNotFoundError as e:
        # Handle missing log file
        logger.error(f"Cannot write to alerts.log: {e}")
        # Re-raise to trigger retry
        raise self.retry(exc=e, countdown=30)
    
    except Exception as e:
        # Catch all other exceptions and retry with backoff
        logger.error(
            f"Alert failed for financing request {financing_id}: {str(e)}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        try:
            # Retry up to 3 times with 60-second delay between attempts
            raise self.retry(exc=e)
        except MaxRetriesExceededError:
            # Log final failure after all retries exhausted
            with open('alerts.log', 'a') as file:
                file.write(
                    f"ALERT FAILED (after 3 retries) for financing request {financing_id}: {str(e)}\n"
                )
            return f"Alert failed after retries: {financing_id}"