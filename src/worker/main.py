import csv
import json
import os
import subprocess
import sys
import time
from typing import Optional


def get_project_root() -> str:
    current_dir = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(current_dir, "../.."))


def atomic_move(src: str, dst: str) -> None:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    os.replace(src, dst)


def pick_one_pending_job(pending_dir: str) -> Optional[str]:
    for name in sorted(os.listdir(pending_dir)):
        if name.endswith('.json') and name.startswith('job-'):
            return os.path.join(pending_dir, name)
    return None


def run_ansible_setup(host: str, user: str, facts_tree_dir: str) -> None:
    os.makedirs(facts_tree_dir, exist_ok=True)
    cmd = [
        'ansible',
        'all',
        '-i', f'{host},',
        '-u', user,
        '-m', 'setup',
        '--tree', facts_tree_dir,
    ]
    env = os.environ.copy()
    env.setdefault('ANSIBLE_HOST_KEY_CHECKING', 'False')
    result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ansible setup failed: {result.stderr.strip() or result.stdout.strip()}")


def extract_normalized_facts(facts: dict) -> dict:
    af = facts.get('ansible_facts', {})
    default_ipv4 = af.get('ansible_default_ipv4', {})
    return {
        'host': af.get('ansible_hostname') or facts.get('inventory_hostname', ''),
        'fqdn': af.get('ansible_fqdn', ''),
        'system': af.get('ansible_system', ''),
        'distribution': af.get('ansible_distribution', ''),
        'distribution_version': af.get('ansible_distribution_version', ''),
        'kernel': af.get('ansible_kernel', ''),
        'architecture': af.get('ansible_architecture', ''),
        'vcpus': af.get('ansible_processor_vcpus', ''),
        'mem_mb_total': af.get('ansible_memtotal_mb', ''),
        'default_ipv4': default_ipv4.get('address', ''),
        'all_ipv4': ';'.join(af.get('ansible_all_ipv4_addresses', []) or []),
        'uptime_seconds': af.get('ansible_uptime_seconds', ''),
        'collected_at': af.get('ansible_date_time', {}).get('iso8601', ''),
    }


def write_host_csv(output_dir: str, host_label: str, row: dict) -> str:
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{host_label}.csv")
    fieldnames = [
        'host', 'fqdn', 'system', 'distribution', 'distribution_version', 'kernel',
        'architecture', 'vcpus', 'mem_mb_total', 'default_ipv4', 'all_ipv4',
        'uptime_seconds', 'collected_at'
    ]
    write_header = not os.path.exists(out_path)
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)
    return out_path


def process_one_job() -> int:
    project_root = get_project_root()
    queue_root = os.path.join(project_root, 'queue')
    pending_dir = os.path.join(queue_root, 'pending')
    processing_dir = os.path.join(queue_root, 'processing')
    done_dir = os.path.join(queue_root, 'done')
    failed_dir = os.path.join(queue_root, 'failed')

    for d in (pending_dir, processing_dir, done_dir, failed_dir):
        os.makedirs(d, exist_ok=True)

    job_path = pick_one_pending_job(pending_dir)
    if not job_path:
        print('No pending jobs')
        return 0

    job_name = os.path.basename(job_path)
    proc_path = os.path.join(processing_dir, job_name)
    try:
        atomic_move(job_path, proc_path)
    except FileNotFoundError:
        return 0

    try:
        with open(proc_path, 'r', encoding='utf-8') as f:
            job = json.load(f)
        host = job.get('host')
        user = job.get('user')
        if not host or not user:
            raise ValueError('Job missing host or user')

        facts_tree_dir = job.get('options', {}).get('tree_dir') or os.path.join(project_root, 'ansible', 'fact_cache')
        print(f"Gathering facts for {host} as {user}")
        run_ansible_setup(host, user, facts_tree_dir)

        facts_file = os.path.join(facts_tree_dir, host)
        if not os.path.exists(facts_file):
            raise FileNotFoundError(f"Facts file not found: {facts_file}")
        with open(facts_file, 'r', encoding='utf-8') as f:
            facts = json.load(f)

        normalized = extract_normalized_facts(facts)
        output_dir = os.path.join(project_root, 'output')
        csv_path = write_host_csv(output_dir, host, normalized)

        job['result'] = {
            'status': 'ok',
            'facts_file': facts_file,
            'csv_file': csv_path
        }
        done_path = os.path.join(done_dir, job_name)
        with open(done_path, 'w', encoding='utf-8') as f:
            json.dump(job, f, ensure_ascii=False, separators=(",", ":"))
        os.remove(proc_path)
        print(f"Done. Wrote CSV: {csv_path}")
        return 1
    except Exception as exc:
        fail_path = os.path.join(failed_dir, job_name)
        try:
            with open(proc_path, 'r', encoding='utf-8') as f:
                job = json.load(f)
        except Exception:
            job = {'raw_path': proc_path}
        job['error'] = {'message': str(exc)}
        with open(fail_path, 'w', encoding='utf-8') as f:
            json.dump(job, f, ensure_ascii=False, separators=(",", ":"))
        os.remove(proc_path)
        print(f"Moved to failed: {fail_path}")
        return -1


if __name__ == '__main__':
    sys.exit(process_one_job())


