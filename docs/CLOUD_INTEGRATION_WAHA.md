# TerraGrid Cloud Integration — WAHA on GCP

Oct 14, 2026 · @Sandesh

## Architecture: where WAHA sits

**Architecture at a glance:**
- Browser -> Cloud Run (frontend + backend, us-central1, scales to zero)
- Cloud Run -> Cloud SQL (PostgreSQL 15, terragrid-db, always-on) via DATABASE_URL
- Cloud Run -> Compute Engine VM (WAHA, e2-micro, always-on, holds the linked WhatsApp session) via HTTPS + X-Api-Key

*(See the live doc for the architecture diagram: https://claude.ai/code/artifact/e8d7a819-4599-45b9-8058-e370498fab77)*

Frontend and backend run together on Cloud Run (`us-central1`), autoscaling to zero between requests. Cloud SQL stays up permanently so data survives restarts. WAHA can't live on Cloud Run for a related reason, except worse: its linked WhatsApp Web session dies the moment its container restarts or sleeps. So it gets its own small, always-on Compute Engine VM, and the backend reaches it over HTTP with an API-key header.

## Prerequisites

- `gcloud` CLI installed and authenticated (`gcloud auth login`), pointed at the same GCP project as the existing Cloud Run backend and Cloud SQL instance (`terragrid-db`, `us-central1`)
- Compute Engine API enabled: `gcloud services enable compute.googleapis.com`
- The existing Cloud Run backend service name and region (`us-central1`) on hand
- A WhatsApp number to scan the QR with (this links WAHA's "default" session to a real phone)
- 2-3 demo recipient numbers decided, in `"Label:phone_number"` form (goes into `WHATSAPP_RECIPIENTS`)

## Step 1 - Provision the VM

```
gcloud compute instances create terragrid-waha-vm \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=20GB \
  --tags=waha-server
```

`e2-micro` in `us-central1` is eligible for GCP's always-free tier (one instance per billing account) - worth confirming on your account before assuming it's free. Keep it in the same region as Cloud Run and Cloud SQL (`us-central1`) to keep latency and any egress cost low.

Don't open port 3000 to the public internet yet - do that (or skip it entirely) in Step 4, once the networking approach is decided.

## Step 2 - Install Docker and run WAHA

SSH in, install Docker, and set up just the `waha` service (the VM doesn't need Postgres/Redis - those already run as Cloud SQL and, if used, Memorystore):

```
gcloud compute ssh terragrid-waha-vm --zone=us-central1-a

# on the VM:
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && newgrp docker

mkdir -p ~/terragrid-waha/waha
cd ~/terragrid-waha
```

Create a minimal `docker-compose.yml` here (copy the `waha` service block from the project's own `docker-compose.yml` - same image, env\_file, volume and port):

```yaml
services:
  waha:
    image: devlikeapro/waha
    container_name: terragrid-waha
    env_file:
      - path: ./waha/.env
        required: false
    ports:
      - "3000:3000"
    volumes:
      - waha_sessions:/app/.sessions
    restart: unless-stopped

volumes:
  waha_sessions:
```

This Linux shell runs the official `$(pwd)` syntax exactly as WAHA's docs show it - the PowerShell quoting problem from local setup doesn't apply here.

## Step 3 - Generate credentials and scan the QR

```
docker run --rm -v "$(pwd)/waha":/app/env devlikeapro/waha init-waha /app/env
docker compose up -d waha
```

`init-waha` prints a dashboard username/password and an API key, and writes them into `waha/.env`. Save that API key - it's `WAHA_API_KEY` for Step 5.

Don't open port 3000 publicly just to scan the QR. Tunnel it instead:

```
gcloud compute ssh terragrid-waha-vm --zone=us-central1-a -- -L 3000:localhost:3000
```

Then open `http://localhost:3000/dashboard` in your own browser, log in with the generated credentials, and scan the QR with the demo WhatsApp number. Once linked, the session persists in the `waha_sessions` volume - the tunnel can be closed and WAHA keeps working.

## Step 4 - Connect Cloud Run to the VM

Two ways to let the backend reach WAHA:

|  | External IP + firewall | VPC connector + internal IP (recommended) |
| --- | --- | --- |
| Setup effort | Lower | One extra `gcloud` command |
| Exposure | Port 3000 open to the internet (or an IP allowlist, which Cloud Run can't guarantee a stable source IP for) | Never leaves Google's internal network |
| Good for | A quick demo you'll tear down | Anything left running |

Recommended - create a Serverless VPC Access connector on the same network as the VM, and attach it to the Cloud Run service:

```
gcloud compute networks vpc-access connectors create terragrid-connector \
  --region=us-central1 --network=default --range=10.8.0.0/28

gcloud run services update terragrid-backend \
  --region=us-central1 \
  --vpc-connector=terragrid-connector \
  --vpc-egress=private-ranges-only
```

Then find the VM's internal IP (`gcloud compute instances describe terragrid-waha-vm --zone=us-central1-a --format='get(networkInterfaces[0].networkIP)'`) and use it as `WAHA_API_URL` in Step 5 - never the external IP. Leave the external-IP route for a throwaway demo only, and close the firewall again afterward if you use it.

## Step 5 - Set Cloud Run env vars

Put the API key in Secret Manager rather than a plain env var - it's the one credential here that actually authenticates against something:

```
printf '%s' '<the WAHA_API_KEY from init-waha>' | gcloud secrets create waha-api-key --data-file=-

gcloud run services update terragrid-backend \
  --region=us-central1 \
  --update-env-vars=WAHA_API_URL=http://<VM-internal-IP>:3000,WAHA_SESSION=default,WHATSAPP_RECIPIENTS="Demo Phone 1:91XXXXXXXXXX,Demo Phone 2:91XXXXXXXXXX" \
  --update-secrets=WAHA_API_KEY=waha-api-key:latest
```

These four map directly to `backend/config.py`'s `WAHA_API_URL` / `WAHA_SESSION` / `WAHA_API_KEY` / `WHATSAPP_RECIPIENTS`. `gcloud run services update` applies env var changes immediately - no rebuild or redeploy through the Cloud Build trigger needed for this step.

## Step 6 - Verify end to end

1. `curl https://<cloud-run-url>/api/v1/prepare/alerts/recipients` - expect `"configured": true` and the 2-3 demo recipients back.
2. Open Agency Alerts in the deployed frontend, pick a recipient, click "Send via WhatsApp", confirm the phone actually receives it.
3. If it fails, the UI's error banner names which layer broke (not configured / not an approved recipient / WAHA unreachable / WAHA rejected the send) - see Troubleshooting below.
4. On the VM: `docker compose logs -f waha` shows the inbound request and WAHA's own send result.
5. On Cloud Run: check the backend logs for the `POST /api/v1/prepare/alerts/send` call if the UI error is vague.

## Ongoing operations

- **Cost**: `e2-micro` may be free (always-free tier, one instance per billing account - confirm on your account); otherwise it's the cheapest machine type, well under $10/month. No new cost added to Cloud Run or Cloud SQL.
- **VM reboot**: `restart: unless-stopped` brings the `waha` container back automatically if the VM reboots. The session survives, since it lives in the `waha_sessions` volume on the VM's own disk.
- **VM recreated/deleted**: the session is gone and needs re-linking (Step 3's QR scan again) - it isn't backed up anywhere else.
- **Monitoring**: none set up yet. Optional next step: a Cloud Monitoring uptime check against the VM, or against WAHA's own health endpoint, so a dead session gets noticed before a demo does.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `docker: invalid reference format` on Windows | PowerShell's `$(pwd)` isn't bash's `$(pwd)` - breaks on the space in a folder name | Use `${PWD}` and backslashes, e.g. `-v "${PWD}\waha:/app/env"`. On the VM this doesn't come up - it's a real Linux shell. |
| UI says "WAHA rejected the send (HTTP 422)" | Session not linked, or not in WORKING state | Re-open the dashboard tunnel (Step 3) and re-scan the QR |
| UI says "Couldn't reach WAHA" | VM stopped, VPC connector not attached to the Cloud Run service, or wrong internal IP in `WAHA_API_URL` | Check the VM is running, `gcloud run services describe terragrid-backend` shows the connector, and the IP matches `gcloud compute instances describe` |
| UI says "WhatsApp sending isn't configured" | `WAHA_API_URL` or `WHATSAPP_RECIPIENTS` missing on Cloud Run | Re-check Step 5's `--update-env-vars` actually applied: `gcloud run services describe terragrid-backend --format='value(spec.template.spec.containers[0].env)'` |
| Send succeeds in logs but the phone gets nothing | Session silently logged out (WhatsApp Web sessions can expire) | Re-scan the QR (Step 3) |
