"""Provision the approved ProofMesh trial project; no billing-account changes."""
import json
import os
import secrets
import subprocess
from pathlib import Path

PROJECT = 'project-9e0a8470-4ba3-458b-885'
REGION = 'asia-south1'
GCLOUD = '/opt/homebrew/bin/gcloud'
ROOT = Path(__file__).resolve().parent.parent
os.environ['CLOUDSDK_CORE_DISABLE_FILE_LOGGING'] = 'true'


def run(*args, capture=False):
    print('gcloud ' + ' '.join(args[:5]), flush=True)
    result = subprocess.run([GCLOUD, *args, '--project=' + PROJECT, '--quiet'], check=True, text=True, capture_output=capture)
    return result.stdout.strip() if capture else None


def exists(*args):
    return subprocess.run([GCLOUD, *args, '--project=' + PROJECT, '--quiet'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


for name in ['runtime', 'tasks', 'build']:
    email = f'proofmesh-{name}@{PROJECT}.iam.gserviceaccount.com'
    if not exists('iam', 'service-accounts', 'describe', email):
        run('iam', 'service-accounts', 'create', 'proofmesh-' + name, '--display-name=ProofMesh ' + name)
runtime = f'proofmesh-runtime@{PROJECT}.iam.gserviceaccount.com'
tasks = f'proofmesh-tasks@{PROJECT}.iam.gserviceaccount.com'
build = f'proofmesh-build@{PROJECT}.iam.gserviceaccount.com'
for role in ['roles/aiplatform.user', 'roles/datastore.user', 'roles/serviceusage.serviceUsageConsumer']:
    run('projects', 'add-iam-policy-binding', PROJECT, '--member=serviceAccount:' + runtime, '--role=' + role, '--condition=None', '--format=none')
run('projects', 'add-iam-policy-binding', PROJECT, '--member=serviceAccount:' + build, '--role=roles/logging.logWriter', '--condition=None', '--format=none')
run('iam', 'service-accounts', 'add-iam-policy-binding', tasks, '--member=serviceAccount:' + runtime, '--role=roles/iam.serviceAccountUser', '--format=none')
if not exists('firestore', 'databases', 'describe', '--database=(default)'):
    run('firestore', 'databases', 'create', '--database=(default)', '--location=' + REGION, '--type=firestore-native')
if not exists('artifacts', 'repositories', 'describe', 'proofmesh', '--location=' + REGION):
    run('artifacts', 'repositories', 'create', 'proofmesh', '--location=' + REGION, '--repository-format=docker')
run('artifacts', 'repositories', 'add-iam-policy-binding', 'proofmesh', '--location=' + REGION, '--member=serviceAccount:' + build, '--role=roles/artifactregistry.writer', '--format=none')
for suffix in ['images', 'builds']:
    bucket = f'gs://{PROJECT}-proofmesh-{suffix}'
    if not exists('storage', 'buckets', 'describe', bucket):
        run('storage', 'buckets', 'create', bucket, '--location=' + REGION, '--uniform-bucket-level-access', '--public-access-prevention')
    role = 'roles/storage.objectUser' if suffix == 'images' else 'roles/storage.objectViewer'
    member = runtime if suffix == 'images' else build
    run('storage', 'buckets', 'add-iam-policy-binding', bucket, '--member=serviceAccount:' + member, '--role=' + role, '--format=none')
    lifecycle = ROOT / 'data' / ('lifecycle-' + suffix + '.json')
    lifecycle.write_text(json.dumps({'rule': [{'action': {'type': 'Delete'}, 'condition': {'age': 1 if suffix == 'images' else 3}}]}))
    run('storage', 'buckets', 'update', bucket, '--lifecycle-file=' + str(lifecycle))
if not exists('tasks', 'queues', 'describe', 'proofmesh-investigations', '--location=' + REGION):
    run('tasks', 'queues', 'create', 'proofmesh-investigations', '--location=' + REGION, '--max-concurrent-dispatches=1', '--max-dispatches-per-second=1', '--max-attempts=3', '--min-backoff=30s', '--max-backoff=60s')
run('tasks', 'queues', 'add-iam-policy-binding', 'proofmesh-investigations', '--location=' + REGION, '--member=serviceAccount:' + runtime, '--role=roles/cloudtasks.enqueuer', '--format=none')
# Each secret is generated once and written only to ignored project-local data.
for name in ['api', 'worker']:
    path = ROOT / 'data' / ('cloud-' + name + '-token')
    if not path.exists():
        path.write_text(secrets.token_urlsafe(36)); path.chmod(0o600)
    secret = 'proofmesh-' + name + '-token'
    if not exists('secrets', 'describe', secret):
        run('secrets', 'create', secret, '--replication-policy=user-managed', '--locations=' + REGION, '--data-file=' + str(path))
    run('secrets', 'add-iam-policy-binding', secret, '--member=serviceAccount:' + runtime, '--role=roles/secretmanager.secretAccessor', '--format=none')
print('Provisioning complete.', flush=True)
