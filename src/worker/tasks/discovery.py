import ansible_runner
import json

def run_ansible_discovery(host, user):
    inventory = f"{host}"
    print(f"Running Ansible setup for {host} as {user}")

    r = ansible_runner.run(
        private_data_dir="/tmp",
        inventory=inventory,
        module="setup",
        host_pattern="all",
        extravars={"ansible_user": user}
    )

    facts = r.get_fact_cache()
    print(json.dumps(facts, indent=2))
    return facts


if __name__ == "__main__":
    run_ansible_discovery("25.44.45.59", "chronia")