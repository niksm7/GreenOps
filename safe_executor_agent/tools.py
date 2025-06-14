from google.cloud import compute_v1
import time

# PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
PROJECT_ID = "greenops-460813"

def is_safe_to_migrate(cpu_forecast: list, mem_forecast: list) -> bool:
    cpu_avg = sum(cpu_forecast) / 7
    mem_avg = sum(mem_forecast) / 7
    return cpu_avg < 30 and mem_avg < 40

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