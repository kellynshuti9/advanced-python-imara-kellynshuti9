from celery import shared_task
import time

@shared_task
def send_alert(financing_id):

    time.sleep(5)

    with open('alerts.log', 'a') as file:
        file.write(
            f"Alert processed for financing request {financing_id}\n"
        )

    return "Done"