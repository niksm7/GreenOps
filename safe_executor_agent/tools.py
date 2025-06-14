from google.cloud import compute_v1, bigquery
import google.auth
from google.auth import credentials
from googleapiclient import discovery
from googleapiclient.errors import HttpError
import uuid
import os
import time

# PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
PROJECT_ID = "greenops-460813"

def create_snapshot(instance_id: str) -> str:
    compute = compute_v1.InstancesClient()
    snapshot_name = f"snap-{uuid.uuid4().hex[:8]}"

    zone = get_instance_zone(instance_id)
    
    # Get disk name
    instance = compute.get(project=PROJECT_ID, zone=zone, instance=instance_id)
    boot_disk = instance.disks[0].source.split("/")[-1]
    
    snapshot = compute_v1.Snapshot(name=snapshot_name)
    disk_client = compute_v1.DisksClient()
    op = disk_client.create_snapshot(
        project=PROJECT_ID,
        zone=zone,
        disk=boot_disk,
        snapshot_resource=snapshot
    )
    op.result()
    return f"projects/{PROJECT_ID}/global/snapshots/{snapshot_name}"


def create_target_instance(current_instance_id: str, instance_type: str, snapshot_link: str = None) -> dict:
    compute = compute_v1.InstancesClient()
    instance_name = f"target-{uuid.uuid4().hex[:8]}"
    
    zone = get_instance_zone(current_instance_id)

    instance = compute_v1.Instance()
    instance.name = instance_name
    instance.machine_type = f"zones/{zone}/machineTypes/{instance_type}"
    instance.zone = zone
    
    # Either boot from snapshot or fresh image
    if snapshot_link:
        source_disk = compute_v1.AttachedDiskInitializeParams(source_snapshot=snapshot_link)
    else:
        source_disk = compute_v1.AttachedDiskInitializeParams(source_image="projects/debian-cloud/global/images/family/debian-11")

    disk = compute_v1.AttachedDisk(boot=True, auto_delete=True, initialize_params=source_disk)
    instance.disks = [disk]
    instance.network_interfaces = [compute_v1.NetworkInterface(name="default")]
    
    op = compute.insert(project=PROJECT_ID, zone=zone, instance_resource=instance)
    op.result()
    return {"instance_id": instance_name}


def is_safe_to_migrate(cpu_forecast: list, mem_forecast: list) -> bool:
    cpu_avg = sum(cpu_forecast) / 7
    mem_avg = sum(mem_forecast) / 7
    return cpu_avg < 30 and mem_avg < 40


def check_instance_status(instance_id: str, timeout_sec: int = 300, interval_sec: int = 10) -> dict:
    compute = compute_v1.InstancesClient()

    zone = get_instance_zone(instance_id)

    elapsed = 0
    while elapsed < timeout_sec:
        instance = compute.get(project=PROJECT_ID, zone=zone, instance=instance_id)
        status = instance.status

        if status == "RUNNING":
            return {
                "status": "success",
                "message": f"Instance {instance_id} is RUNNING.",
                "instance_status": status
            }

        time.sleep(interval_sec)
        elapsed += interval_sec

    return {
        "status": "timeout",
        "message": f"Instance {instance_id} did not reach RUNNING state within {timeout_sec} seconds.",
        "instance_status": status
    }


def delete_instance(instance_id: str) -> dict:
    compute = compute_v1.InstancesClient()

    try:
        operation = compute.delete(project=PROJECT_ID, zone=get_instance_zone(instance_id), instance=instance_id)
        operation.result()
        return {
            "status": "success",
            "message": f"Instance {instance_id} deleted successfully."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to delete instance {instance_id}: {str(e)}"
        }

def get_instance_zone(instance_id: str) -> str:
    compute = compute_v1.InstancesClient()

    for zone, response in compute.aggregated_list(request=compute_v1.AggregatedListInstancesRequest(project=PROJECT_ID)):
        for instance in response.instances or []:
            if instance.name == instance_id:
                return instance.zone.split("/")[-1]

    raise Exception(f"Zone not found for instance: {instance_id}")

def wait_for_status(instance_client, project, zone, instance_name, expected_status, timeout_sec=300):
    elapsed = 0
    while elapsed < timeout_sec:
        instance = instance_client.get(project=project, zone=zone, instance=instance_name)
        current_status = instance.status
        print(f"Current status: {current_status}")
        if current_status == expected_status:
            return True
        time.sleep(5)
        elapsed += 5
    raise TimeoutError(f"Instance did not reach {expected_status} state in {timeout_sec} seconds.")


def change_machine_type(instance_id: str, new_machine_type: str):

    zone = get_instance_zone(instance_id)
    instance_client = compute_v1.InstancesClient()

    print("🔄 Stopping instance...")
    stop_op = instance_client.stop(project=PROJECT_ID, zone=zone, instance=instance_id)
    stop_op.result()  # wait for stop to initiate
    wait_for_status(instance_client, PROJECT_ID, zone, instance_id, "TERMINATED")
    print("✅ Instance stopped.")

    # Set machine type
    machine_type_uri = f"projects/{PROJECT_ID}/zones/{zone}/machineTypes/{new_machine_type}"
    req = compute_v1.InstancesSetMachineTypeRequest(machine_type=machine_type_uri)
    
    print(f"⚙️ Setting machine type to {new_machine_type}...")
    op = instance_client.set_machine_type(
        project=PROJECT_ID,
        zone=zone,
        instance=instance_id,
        instances_set_machine_type_request_resource=req,
    )
    op.result()
    print("✅ Machine type updated successfully.")

    print("🚀 Starting instance...")
    start_op = instance_client.start(project=PROJECT_ID, zone=zone, instance=instance_id)
    start_op.result()
    wait_for_status(instance_client, PROJECT_ID, zone, instance_id, "RUNNING")
    print("✅ Instance is running with new machine type.")


print(change_machine_type("instance-20250614-105928", "e2-micro"))