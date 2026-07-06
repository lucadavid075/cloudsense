import boto3
from typing import Optional
from app.utils.config import settings

# Approximate monthly costs for common resource types
RESOURCE_COSTS = {
    "ebs_volume_gp2": 0.10,   # per GB/month
    "ebs_volume_gp3": 0.08,
    "elastic_ip": 3.60,        # per month when unattached
    "nat_gateway": 32.40,      # per month base
}


def get_ec2_client(region: Optional[str] = None):
    return boto3.client(
        "ec2",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=region or settings.aws_default_region,
    )


def get_all_regions() -> list[str]:
    """Get list of enabled AWS regions."""
    client = get_ec2_client()
    try:
        response = client.describe_regions(Filters=[{"Name": "opt-in-status", "Values": ["opt-in-not-required", "opted-in"]}])
        return [r["RegionName"] for r in response["Regions"]]
    except Exception:
        return [settings.aws_default_region]


def scan_unattached_ebs_volumes(region: Optional[str] = None) -> list[dict]:
    """Find EBS volumes not attached to any instance."""
    client = get_ec2_client(region)
    region_name = region or settings.aws_default_region

    try:
        response = client.describe_volumes(
            Filters=[{"Name": "status", "Values": ["available"]}]
        )
    except Exception as e:
        return []

    results = []
    for vol in response.get("Volumes", []):
        size_gb = vol["Size"]
        vol_type = vol.get("VolumeType", "gp2")
        cost_per_gb = RESOURCE_COSTS.get(f"ebs_volume_{vol_type}", 0.10)
        monthly_cost = size_gb * cost_per_gb

        name = next(
            (t["Value"] for t in vol.get("Tags", []) if t["Key"] == "Name"),
            "Unnamed"
        )

        results.append({
            "resource_type": "ebs_volume",
            "resource_id": vol["VolumeId"],
            "region": region_name,
            "estimated_monthly_cost": round(monthly_cost, 2),
            "details": {
                "name": name,
                "size_gb": size_gb,
                "volume_type": vol_type,
                "created": vol["CreateTime"].isoformat(),
                "state": vol["State"],
            },
        })

    return results


def scan_unattached_elastic_ips(region: Optional[str] = None) -> list[dict]:
    """Find Elastic IPs not associated with any resource."""
    client = get_ec2_client(region)
    region_name = region or settings.aws_default_region

    try:
        response = client.describe_addresses()
    except Exception:
        return []

    results = []
    for addr in response.get("Addresses", []):
        # Unattached if no AssociationId
        if "AssociationId" not in addr:
            results.append({
                "resource_type": "elastic_ip",
                "resource_id": addr["AllocationId"],
                "region": region_name,
                "estimated_monthly_cost": RESOURCE_COSTS["elastic_ip"],
                "details": {
                    "public_ip": addr.get("PublicIp"),
                    "allocation_id": addr.get("AllocationId"),
                    "domain": addr.get("Domain"),
                },
            })

    return results


def scan_stopped_ec2_instances(region: Optional[str] = None) -> list[dict]:
    """Find EC2 instances that are stopped but still have attached EBS volumes."""
    client = get_ec2_client(region)
    region_name = region or settings.aws_default_region

    try:
        response = client.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
        )
    except Exception:
        return []

    results = []
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            name = next(
                (t["Value"] for t in instance.get("Tags", []) if t["Key"] == "Name"),
                "Unnamed"
            )
            volume_ids = [
                mapping["Ebs"]["VolumeId"]
                for mapping in instance.get("BlockDeviceMappings", [])
                if "Ebs" in mapping
            ]

            results.append({
                "resource_type": "ec2_stopped",
                "resource_id": instance["InstanceId"],
                "region": region_name,
                "estimated_monthly_cost": 0.0,  # No compute cost, but EBS still charged
                "details": {
                    "name": name,
                    "instance_type": instance.get("InstanceType"),
                    "stopped_since": instance.get("StateTransitionReason", "Unknown"),
                    "attached_volumes": volume_ids,
                    "volume_count": len(volume_ids),
                },
            })

    return results


def run_full_resource_scan(region: Optional[str] = None) -> dict:
    """Run all idle resource checks and return combined results."""
    ebs = scan_unattached_ebs_volumes(region)
    eips = scan_unattached_elastic_ips(region)
    stopped = scan_stopped_ec2_instances(region)

    all_resources = ebs + eips + stopped
    total_waste = sum(r["estimated_monthly_cost"] for r in all_resources)

    return {
        "resources": all_resources,
        "summary": {
            "total_idle_resources": len(all_resources),
            "unattached_ebs_volumes": len(ebs),
            "unattached_elastic_ips": len(eips),
            "stopped_ec2_instances": len(stopped),
            "estimated_monthly_waste_usd": round(total_waste, 2),
        },
    }


def get_resource_summary_for_agent(region: Optional[str] = None) -> str:
    """Return plain-text idle resource summary for the AI agent."""
    scan = run_full_resource_scan(region)
    s = scan["summary"]
    resources = scan["resources"]

    lines = [
        "Idle Resource Scan Results:",
        f"  Total idle resources: {s['total_idle_resources']}",
        f"  Unattached EBS volumes: {s['unattached_ebs_volumes']}",
        f"  Unattached Elastic IPs: {s['unattached_elastic_ips']}",
        f"  Stopped EC2 instances: {s['stopped_ec2_instances']}",
        f"  Estimated monthly waste: ${s['estimated_monthly_waste_usd']}",
    ]

    if resources:
        lines.append("\nDetails:")
        for r in resources[:10]:  # Cap at 10 for token efficiency
            lines.append(f"  - [{r['resource_type']}] {r['resource_id']} ({r['region']}) — ${r['estimated_monthly_cost']}/mo")

    return "\n".join(lines)
