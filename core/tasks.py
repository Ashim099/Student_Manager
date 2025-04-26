from background_task import background
from django.core.mail import send_mail
from .models import Reminder
import logging

logger = logging.getLogger(__name__)

@background(schedule=0)
def send_reminder_email(reminder_id):
    try:
        reminder = Reminder.objects.get(id=reminder_id)
        if reminder.is_sent:
            logger.info(f"Email already sent for reminder {reminder.id}")
            return

        if not reminder.student.email:
            logger.error(f"No email found for student {reminder.student.username} for reminder {reminder.id}")
            return

        subject = f"Reminder: {reminder.title}"
        message = f"Dear {reminder.student.username},\n\nThis is a reminder for: {reminder.title}\nScheduled for: {reminder.reminder_date}\n\nBest regards,\nStudent Manager Team"
        recipient = reminder.student.email

        send_mail(
            subject=subject,
            message=message,
            from_email='ashimpoudel1357@gmail.com',
            recipient_list=[recipient],
            fail_silently=False,
        )

        reminder.is_sent = True
        reminder.save()
        logger.info(f"Email sent for reminder {reminder.id} to {recipient}")
    except Reminder.DoesNotExist:
        logger.error(f"Reminder {reminder_id} not found.")
    except Exception as e:
        logger.error(f"Failed to send email for reminder {reminder_id}: {str(e)}")