
import os
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class CloudWatchMonitor:
    def __init__(self):
        self.region = (
            os.getenv("AWS_REGION")
            or os.getenv("AWS_DEFAULT_REGION")
            or "ap-south-2"
        )

        self.instance_id = os.getenv("RESQCLOUD_EC2_INSTANCE_ID")

        try:
            self.threshold = float(
                os.getenv("RESQCLOUD_CPU_THRESHOLD", "80")
            )
        except ValueError as exc:
            raise ValueError(
                "RESQCLOUD_CPU_THRESHOLD must be a number."
            ) from exc

        if not 0 <= self.threshold <= 100:
            raise ValueError(
                "CPU threshold must be between 0 and 100."
            )

        self.client = boto3.client(
            "cloudwatch",
            region_name=self.region
        )

    def get_ec2_cpu_utilization(self):
        if not self.instance_id:
            raise ValueError(
                "RESQCLOUD_EC2_INSTANCE_ID is not configured."
            )

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=20)

        try:
            response = self.client.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[
                    {
                        "Name": "InstanceId",
                        "Value": self.instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=["Average", "Maximum"]
            )

        except (ClientError, BotoCoreError) as exc:
            raise RuntimeError(
                f"CloudWatch request failed: {exc}"
            ) from exc

        datapoints = response.get("Datapoints", [])

        if not datapoints:
            return {
                "instance_id": self.instance_id,
                "region": self.region,
                "metric": "CPUUtilization",
                "data_available": False,
                "message": (
                    "No CPU datapoints were returned for "
                    "the selected time window."
                ),
                "checked_at": end_time.isoformat()
            }

        latest = max(
            datapoints,
            key=lambda point: point["Timestamp"]
        )

        average_cpu = round(latest["Average"], 2)
        maximum_cpu = round(latest["Maximum"], 2)
        is_critical = average_cpu >= self.threshold

        return {
            "instance_id": self.instance_id,
            "region": self.region,
            "metric": "CPUUtilization",
            "data_available": True,
            "cpu_average_percent": average_cpu,
            "cpu_maximum_percent": maximum_cpu,
            "threshold_percent": self.threshold,
            "healthy": not is_critical,
            "status": "critical" if is_critical else "healthy",
            "datapoint_time": latest["Timestamp"].isoformat(),
            "checked_at": end_time.isoformat()
        }