import os
from datetime import datetime, timezone

import boto3


UNHEALTHY_STATUSES = {
    "unhealthy",
    "critical",
    "failed",
    "down",
    "error",
}


def evaluate_status(status: str) -> dict:
    normalized = status.strip().lower()

    if not normalized:
        raise ValueError("Status cannot be empty.")

    return {
        "status": normalized,
        "healthy": normalized not in UNHEALTHY_STATUSES,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def send_sns_alert(
    component: str,
    status: str,
    message: str,
    incident_id: int,
) -> dict:
    topic_arn = os.getenv("RESQCLOUD_SNS_TOPIC_ARN")
    region = os.getenv("AWS_REGION", "ap-south-2")

    if not topic_arn:
        return {
            "sent": False,
            "reason": "SNS topic ARN is not configured.",
        }

    client = boto3.client("sns", region_name=region)

    response = client.publish(
        TopicArn=topic_arn,
        Subject=f"ResQCloud Incident #{incident_id}",
        Message=(
            f"ResQCloud detected an incident.\n\n"
            f"Incident ID: {incident_id}\n"
            f"Component: {component}\n"
            f"Status: {status}\n"
            f"Details: {message}\n"
        ),
    )

    return {
        "sent": True,
        "message_id": response.get("MessageId"),
    }