# Translation API for OCI

Translates between multiple language pairs using OCI GenAI models. Built for online lottery, gambling, and finance domains with a domain-specific glossary.

## Deployment Options

### Option A — OCI Functions (Serverless)
Sync-only translation behind OCI API Gateway.

### Option B — FastAPI (Docker)
Sync and streaming (SSE) translation.

## Quick Start (Option B — Local)

```bash
# Set environment variables on linux
export OCI_COMPARTMENT_ID="ocid1.compartment.oc1....."
export OCI_CONFIG_FILE="~/.oci/config"

# Set environment variables on windows
$env:OCI_COMPARTMENT_ID = "ocid1.compartment.oc1..aaaaaaaax6vcsmyeticn...."
$env:OCI_CONFIG_FILE = "C:\Users\xxxx\.oci\config"


# Install dependencies
pip install -r option_b_fastapi/requirements.txt

# Run
uvicorn option_b_fastapi.main:app --reload
```

## API Usage

### Sync Translation
```bash
curl -X POST http://localhost:8000/translate \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Place your wager on the next jackpot draw.",
    "source_language": "english",
    "target_language": "spanish-mx"
  }'
```

### Streaming (SSE)
```bash
curl -N -X POST http://localhost:8000/translate/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Place your wager on the next jackpot draw.",
    "source_language": "english",
    "target_language": "spanish-mx"
  }'
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OCI_COMPARTMENT_ID` | (required) | OCI compartment OCID |
| `OCI_GENAI_ENDPOINT` | `https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com` | GenAI endpoint |
| `OCI_DEFAULT_MODEL` | `cohere.command-a-03-2025` | Default model ID |
| `OCI_CONFIG_FILE` | `~/.oci/config` | OCI config file path |
| `OCI_CONFIG_PROFILE` | `DEFAULT` | OCI config profile |
| `MAX_TOKENS` | `2048` | Max output tokens |
| `TEMPERATURE` | `0.0` | Sampling temperature |
| `TOP_P` | `0.8` | Top-p sampling |
| `OCI_AUTH` | `auto` | Set to `api_key` to skip Resource Principals and use `~/.oci/config` directly |

## Supported Language Pairs
`english`, `german`, `spanish-mx`, `polish`, `portuguese-br`, `swedish`

| Source / Target | English | German | Spanish (MX) | Polish | Portuguese (BR) | Swedish |
|-----------------|:-------:|:------:|:------------:|:------:|:---------------:|:-------:|
| **English**     |    —    |   ✓    |      ✓       |   ✓    |        ✓        |    ✓    |
| **German**      |    ✓    |   —    |      ✓       |   ✓    |        ✓        |    ✓    |
| **Spanish (MX)**|    ✓    |   ✓    |      —       |   ✓    |                 |    ✓    |
| **Polish**      |    ✓    |   ✓    |      ✓       |   —    |                 |         |
| **Portuguese (BR)** | ✓   |   ✓    |              |        |        —        |         |
| **Swedish**     |    ✓    |   ✓    |      ✓       |        |                 |    —    |

## Supported Models
Any OCI GenAI on-demand model. The API auto-detects the correct format from the model ID: GENERIC (Llama/Meta), COHERE (Command R/R+), or COHEREV2 (Command A).

## Tests

```bash
pip install pytest
pytest tests/
```

The test suite validates:

- **Every allowed language pair** in both directions (22 parametrized cases covering all 11 pairs)
- **Invalid pair rejection** — pairs not in `ALLOWED_PAIRS` (e.g. Polish to Portuguese-BR) are rejected with a clear error
- **Input validation** — unsupported languages, same source/target, empty text
- **OCI chat body construction** — correct API format selection (GENERIC for Llama, COHERE for Command R/R+, COHEREV2 for Command A), stream flag, system/user message structure
- **Sync translation** — end-to-end with mocked OCI client

## Adding a Language Pair

Three files need updating:

1. **`core/config.py`** — Add the language key to `SUPPORTED_LANGUAGES` (if new) and the pair to `ALLOWED_PAIRS`:
   ```python
   SUPPORTED_LANGUAGES = {"english", "german", ..., "italian"}

   ALLOWED_PAIRS: set[frozenset[str]] = {
       ...,
       frozenset({"english", "italian"}),
   }
   ```

2. **`core/glossary.py`** — Add a translation for the new language to each term in `GLOSSARY`:
   ```python
   "jackpot": {
       ...,
       "italian": "jackpot",
   },
   ```

3. **`tests/test_models.py`** — Add the new pair (both directions) to the `test_valid_language_pair` parametrize list, and remove it from `test_invalid_language_pair_raises` if it was previously listed there.

## Deploying Option B — Container Instance + Load Balancer

Always-on container (no cold starts) behind a flexible load balancer. The container authenticates to OCI GenAI via API key (`~/.oci/config` baked into the deploy image).

### Prerequisites

- **OCI CLI** configured locally (`~/.oci/config`) — Terraform uses this to provision resources, and the API key is baked into the deploy image
- **Docker** running locally (Colima or Docker Desktop)
- **Terraform** installed
- **OCIR access** — logged into OCI Container Registry (`docker login <region-key>.ocir.io`)
- **OCIR repo** — create the repo before first push: `oci artifacts container repository create --compartment-id <compartment-ocid> --display-name translate-api`
- **IAM permissions** — your user/group must be able to create container instances and load balancers in the target compartment

You will need the following from your OCI tenancy:

| Value | Where to find it |
|---|---|
| Compartment OCID | Identity > Compartments |
| Subnet OCID | Networking > VCNs > Subnets (public subnet with ingress on ports 443 and 8000) |
| OCIR namespace | Container Registry > Settings, or run `oci os ns get` |
| Region key | e.g. `fra` for eu-frankfurt-1, `lhr` for uk-london-1 |

### Step 1 — Build and push the Docker image

The deploy Dockerfile (`Dockerfile.deploy`) bakes in OCI API key credentials from a staging directory. First, prepare the credentials:

```bash
# Stage OCI config with container-friendly key path on linux
mkdir -p .oci_deploy
sed 's|key_file=.*|key_file=/root/.oci/oci_api_key.pem|' ~/.oci/config > .oci_deploy/config
cp ~/.oci/oci_api_key.pem .oci_deploy/oci_api_key.pem

# Stage OCI config with container-friendly key path on windows
New-Item -ItemType Directory -Force .oci_deploy | Out-Null

(Get-Content "C:\Users\Pruvost\.oci\config") `
  -replace 'key_file=.*', 'key_file=/root/.oci/oci_api_key.pem' `
  | Set-Content .oci_deploy\config

Copy-Item "C:\Travail\Travail2025\Demos\SshKeys\NewAPIKeys\MyNewPrivateAPIKey.pem" .oci_deploy\oci_api_key.pem

```

Then build for AMD64 (OCI Container Instances use x86), tag, and push:

```bash
# Build for AMD64
docker build --platform linux/amd64 -f option_b_fastapi/Dockerfile.deploy -t translate-api:deploy .
ex (no need tag after here) : docker build --platform linux/amd64 -f option_b_fastapi/Dockerfile.deploy -t cdg.ocir.io/frsxwtjslf35/translate-api:2.0.0 .

# Tag for OCIR if needed
docker tag translate-api:deploy <region-key>.ocir.io/<namespace>/translate-api:latest
ex : docker tag translate-api:deploy fra.ocir.io/frsxwtjslf35/translate-api:latest

# Push
docker push <region-key>.ocir.io/<namespace>/translate-api:latest
ex : docker push fra.ocir.io/frsxwtjslf35/translate-api:latest
```

The `.oci_deploy/` directory is gitignored — credentials are never committed.

### Step 2 — Deploy with Terraform

```bash
cd terraform/option_b_container
terraform init
terraform apply \
  -var compartment_id="ocid1.compartment.oc1....." \
  -var subnet_id="ocid1.subnet.oc1....." \
  -var container_image="<region-key>.ocir.io/<namespace>/translate-api:latest" \
  -var oci_compartment_id_env="ocid1.compartment.oc1....."
```

Optional variables:

| Variable | Default | Description |
|---|---|---|
| `container_count` | `1` | Number of container instances (spread across ADs) |
| `container_ocpus` | `1` | OCPUs per instance |
| `container_memory_gb` | `2` | Memory (GB) per instance |
| `oci_default_model` | `cohere.command-a-03-2025` | Default model passed to the container |
| `oci_genai_endpoint` | Frankfurt endpoint | GenAI inference endpoint |

### Step 3 — Verify

Terraform outputs the load balancer IP. Test it:

```bash
curl -X POST http://<load-balancer-ip>/translate \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Place your wager on the next jackpot draw.",
    "source_language": "english",
    "target_language": "german"
  }'
```
Note : Remember that you must wait a few seconds to allow the LB to discover the backends. If you do a request just after the stack apply you can get "502 Bad Gateway". Just wait then... 

### Updating the container

After code changes, rebuild, push, then restart the container instance:

```bash
docker build --platform linux/amd64 -f option_b_fastapi/Dockerfile.deploy -t translate-api:deploy .
docker tag translate-api:deploy <region-key>.ocir.io/<namespace>/translate-api:latest
docker push <region-key>.ocir.io/<namespace>/translate-api:latest

# Restart picks up the new :latest image
oci container-instances container-instance restart \
  --container-instance-id <instance-ocid>
```

## Estimated Costs (Option B)

| Resource | Spec | ~Monthly (USD) |
|---|---|---|
| Container Instance | 1 OCPU, 2 GB RAM, always-on | ~$27 |
| Flexible Load Balancer | 10 Mbps minimum | ~$10 |
| GenAI inference (Command A) | per request | ~$0.0015/1K input tokens, ~$0.007/1K output tokens |
| OCIR image storage | | negligible |

**Fixed infrastructure: ~$37/month** plus GenAI usage. For light usage (a few hundred translations/day), GenAI adds a few dollars/month. To save costs when not in use, tear down with `terraform destroy` and redeploy when needed.

## Deploying Option C — x Container Instances + Load Balancer
Do the same step for building the docker image and pushing it to OCIR
Look at the Readme in the option_c_xcontainers. Click on Deploy to Oracle Cloud then you will create a terraform stack that will deploy x CI automatically. The CI are in a private subnet but you can reach them via a LB in a public subnet.

Note that you need before :
- a VCN with a public and a private subnet (Open port 8000 on the 2 subnets with security rules
). Use the VCN wizard to get one quickly.
- a secret in Vault for being authorize to get image from registry. 
The secret should use the username and token that you use to push to OCIR. Ex :
{
"username": "My_user",
"password": "My_Password"
}

After deploying do the same test than Option B to check that everything is OK.

## Docker (Local Development)

For local testing without Terraform:

```bash
docker build -f option_b_fastapi/Dockerfile -t translate-api .
docker run -p 8000:8000 \
  -v ~/.oci:/root/.oci:ro \
  -e OCI_COMPARTMENT_ID="..." \
  translate-api
```

## Terraform — Option A (OCI Functions + API Gateway)

Serverless alternative (has cold starts):

```bash
cd terraform/option_a_functions
terraform init
terraform apply \
  -var compartment_id="..." \
  -var function_id="..." \
  -var subnet_id="..."
```
