import os
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class CloudWatchMonitor:
    """
    ResQCloud CloudWatch monitoring service.

    Monitors:
    - EC2 CPU utilization
    - EC2 memory utilization through CloudWatch Agent
    - EC2 disk utilization through CloudWatch Agent

    Thresholds:
    - CPU: 80%
    - Memory: 80%
    - Disk: 85%
    """

    CPU_THRESHOLD = 80.0
    MEMORY_THRESHOLD = 80.0
    DISK_THRESHOLD = 85.0

    def __init__(self):
        self.region = (
            os.getenv("AWS_REGION")
            or os.getenv("AWS_DEFAULT_REGION")
            or "ap-south-2"
        )

        self.instance_id = os.getenv(
            "RESQCLOUD_EC2_INSTANCE_ID",
            "i-0267568803e75035c"
        ).strip()

        self.cloudwatch = boto3.client(
            "cloudwatch",
            region_name=self.region
        )

    # =========================================================
    # GENERIC CLOUDWATCH QUERY
    # =========================================================

    def _get_metric_statistics(
        self,
        namespace,
        metric_name,
        dimensions,
        period=300,
        statistic="Average",
        minutes=30
    ):
        end_time = datetime.now(timezone.utc)

        start_time = (
            end_time -
            timedelta(minutes=minutes)
        )

        response = self.cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=[statistic]
        )

        datapoints = response.get(
            "Datapoints",
            []
        )

        datapoints.sort(
            key=lambda item: item["Timestamp"]
        )

        return [
            {
                "timestamp": point[
                    "Timestamp"
                ].isoformat(),
                "value": float(
                    point.get(
                        statistic,
                        0
                    )
                )
            }
            for point in datapoints
            if point.get(statistic) is not None
        ]

    # =========================================================
    # CPU
    # =========================================================

    def get_ec2_cpu_utilization(self):
        try:
            metrics = self._get_metric_statistics(
                namespace="AWS/EC2",
                metric_name="CPUUtilization",
                dimensions=[
                    {
                        "Name": "InstanceId",
                        "Value": self.instance_id
                    }
                ]
            )

            if not metrics:
                return {
                    "data_available": False,
                    "instance_id": self.instance_id,
                    "region": self.region,
                    "message": (
                        "No CPU CloudWatch data "
                        "is currently available."
                    )
                }

            values = [
                item["value"]
                for item in metrics
            ]

            average_cpu = (
                sum(values) /
                len(values)
            )

            latest_timestamp = (
                metrics[-1]["timestamp"]
            )

            return {
                "data_available": True,
                "instance_id": self.instance_id,
                "region": self.region,
                "cpu_average_percent": round(
                    average_cpu,
                    2
                ),
                "threshold_percent":
                    self.CPU_THRESHOLD,
                "healthy":
                    average_cpu <=
                    self.CPU_THRESHOLD,
                "metric_timestamp":
                    latest_timestamp
            }

        except (
            ClientError,
            BotoCoreError,
            Exception
        ) as exc:

            return {
                "data_available": False,
                "instance_id": self.instance_id,
                "region": self.region,
                "message": str(exc)
            }

    # =========================================================
    # MEMORY
    # =========================================================

    def get_memory_utilization(self):
        image_id = os.getenv(
            "RESQCLOUD_EC2_IMAGE_ID",
            ""
        ).strip()

        instance_type = os.getenv(
            "RESQCLOUD_EC2_INSTANCE_TYPE",
            ""
        ).strip()

        # Actual CloudWatch Agent dimensions:
        # ImageId + InstanceId + InstanceType
        dimensions = [
            {
                "Name": "ImageId",
                "Value": image_id
            },
            {
                "Name": "InstanceId",
                "Value": self.instance_id
            },
            {
                "Name": "InstanceType",
                "Value": instance_type
            }
        ]

        try:
            if not all(
                dimension["Value"]
                for dimension in dimensions
            ):
                return {
                    "data_available": False,
                    "instance_id": self.instance_id,
                    "region": self.region,
                    "message": (
                        "Required EC2 memory metric "
                        "dimensions are not configured."
                    )
                }

            metrics = self._get_metric_statistics(
                namespace="CWAgent",
                metric_name="mem_used_percent",
                dimensions=dimensions
            )

            if not metrics:
                return {
                    "data_available": False,
                    "instance_id": self.instance_id,
                    "region": self.region,
                    "message": (
                        "No memory CloudWatch Agent "
                        "data is available."
                    )
                }

            values = [
                item["value"]
                for item in metrics
            ]

            average_memory = (
                sum(values) /
                len(values)
            )

            return {
                "data_available": True,
                "instance_id": self.instance_id,
                "region": self.region,
                "memory_average_percent": round(
                    average_memory,
                    2
                ),
                "threshold_percent":
                    self.MEMORY_THRESHOLD,
                "healthy":
                    average_memory <=
                    self.MEMORY_THRESHOLD,
                "metric_timestamp":
                    metrics[-1]["timestamp"]
            }

        except (
            ClientError,
            BotoCoreError,
            Exception
        ) as exc:

            return {
                "data_available": False,
                "instance_id": self.instance_id,
                "region": self.region,
                "message": str(exc)
            }

    # =========================================================
    # DISK
    # =========================================================

    def get_disk_utilization(self):
        image_id = os.getenv(
            "RESQCLOUD_EC2_IMAGE_ID",
            ""
        ).strip()

        instance_type = os.getenv(
            "RESQCLOUD_EC2_INSTANCE_TYPE",
            ""
        ).strip()

        # Actual CloudWatch Agent disk dimensions:
        # ImageId + InstanceId + InstanceType
        # + device + fstype + path
        dimensions = [
            {
                "Name": "ImageId",
                "Value": image_id
            },
            {
                "Name": "InstanceId",
                "Value": self.instance_id
            },
            {
                "Name": "InstanceType",
                "Value": instance_type
            },
            {
                "Name": "device",
                "Value": "nvme0n1p1"
            },
            {
                "Name": "fstype",
                "Value": "ext4"
            },
            {
                "Name": "path",
                "Value": "/"
            }
        ]

        try:
            if not all(
                dimension["Value"]
                for dimension in dimensions
            ):
                return {
                    "data_available": False,
                    "instance_id": self.instance_id,
                    "region": self.region,
                    "message": (
                        "Required EC2 disk metric "
                        "dimensions are not configured."
                    )
                }

            metrics = self._get_metric_statistics(
                namespace="CWAgent",
                metric_name="disk_used_percent",
                dimensions=dimensions
            )

            if not metrics:
                return {
                    "data_available": False,
                    "instance_id": self.instance_id,
                    "region": self.region,
                    "message": (
                        "No disk CloudWatch Agent "
                        "data is available."
                    )
                }

            values = [
                item["value"]
                for item in metrics
            ]

            average_disk = (
                sum(values) /
                len(values)
            )

            return {
                "data_available": True,
                "instance_id": self.instance_id,
                "region": self.region,
                "disk_average_percent": round(
                    average_disk,
                    2
                ),
                "threshold_percent":
                    self.DISK_THRESHOLD,
                "healthy":
                    average_disk <=
                    self.DISK_THRESHOLD,
                "metric_timestamp":
                    metrics[-1]["timestamp"]
            }

        except (
            ClientError,
            BotoCoreError,
            Exception
        ) as exc:

            return {
                "data_available": False,
                "instance_id": self.instance_id,
                "region": self.region,
                "message": str(exc)
            }

    # =========================================================
    # UNIFIED HEALTH CHECK
    # =========================================================

    def run_health_check(self):
        cpu = self.get_ec2_cpu_utilization()
        memory = self.get_memory_utilization()
        disk = self.get_disk_utilization()

        checks = {
            "cpu": cpu,
            "memory": memory,
            "disk": disk
        }

        failed_checks = []

        # CPU failure
        if (
            cpu.get("data_available")
            and not cpu.get("healthy")
        ):
            failed_checks.append({
                "metric": "cpu",
                "value": cpu.get(
                    "cpu_average_percent"
                ),
                "threshold": cpu.get(
                    "threshold_percent"
                )
            })

        # Memory failure
        if (
            memory.get("data_available")
            and not memory.get("healthy")
        ):
            failed_checks.append({
                "metric": "memory",
                "value": memory.get(
                    "memory_average_percent"
                ),
                "threshold": memory.get(
                    "threshold_percent"
                )
            })

        # Disk failure
        if (
            disk.get("data_available")
            and not disk.get("healthy")
        ):
            failed_checks.append({
                "metric": "disk",
                "value": disk.get(
                    "disk_average_percent"
                ),
                "threshold": disk.get(
                    "threshold_percent"
                )
            })

        # A metric being unavailable is not currently
        # treated as a threshold failure.
        #
        # The important requirement at this stage is
        # that CloudWatch data is successfully available
        # for CPU, memory and disk.

        data_available = any([
            cpu.get("data_available"),
            memory.get("data_available"),
            disk.get("data_available")
        ])

        healthy = (
            len(failed_checks) == 0
        )

        return {
            "healthy": healthy,
            "instance_id": self.instance_id,
            "region": self.region,
            "checks": checks,
            "failed_checks": failed_checks,
            "data_available": data_available,
            "checked_at":
                datetime.now(
                    timezone.utc
                ).isoformat()
        }