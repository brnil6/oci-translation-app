# Translation API for OCI

Translates between multiple language pairs using OCI GenAI models. Built for online lottery, gambling, and finance domains with a domain-specific glossary.

## Deployment Options

### Option A [DEPRECATED - DO NOT USED] — OCI Functions (Serverless)
Sync-only translation behind OCI API Gateway.
This code was not updated to follow all new features and will probably failed if used.

### Option B — FastAPI (Docker)
Sync and streaming (SSE) translation.

## Quick Start (Option B — Local)

Prerequisites : 
1) Your OCI user/group should be authorized to use all the services needed on OCI (Container Instances, Load Balancer, Vault, Stack Resources Manager, ...)

2) Install OCI CLI and configure it for your Tenant. [https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm]

3) Create a bucket with the name bucket-glossary et in this bucket upload a file named glossary.json (look at the exemple in this project). Be carefull do not make error with json so use a json validator before uploading the file (ex : https://jsonformatter.curiousconcept.com/)

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
And so on...

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

Set the variable for having real call to OCI Bucket to get the glossary : export RUN_OCI_INTEGRATION_TESTS=1 [Linux] or $env:RUN_OCI_INTEGRATION_TESTS="1" [Windows]

You can run the test with : python.exe -m pytest -q

The test suite validates:

- **Every allowed language pair** in both directions (22 parametrized cases covering all 11 pairs)
- **Invalid pair rejection** — pairs not in `ALLOWED_PAIRS` (e.g. Polish to Portuguese-BR) are rejected with a clear error
- **Input validation** — unsupported languages, same source/target, empty text
- **OCI chat body construction** — correct API format selection (GENERIC for Llama, COHERE for Command R/R+, COHEREV2 for Command A), stream flag, system/user message structure
- **Sync translation** — end-to-end with mocked OCI client or real call
- **Glossary use** - check that glossary is downloaded from OCI Bucket and used

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

2. **`core/glossary.json`** — is never used locally an must be uploaded to the OCI Bucket. The glossary is refreshed every 5 minutes from the OCI Bucket.
   

3. **`tests/test_models.py`** — Add the new pair (both directions) to the `test_valid_language_pair` parametrize list, and remove it from `test_invalid_language_pair_raises` if it was previously listed there.

## Deploying Option B — Container Instance + Load Balancer

Always-on container (no cold starts) behind a flexible load balancer. The container authenticates to OCI GenAI via API key (`~/.oci/config` baked into the deploy image).

### Prerequisites

- **Docker** running locally (Colima or Docker Desktop or Rancher Desktop or .)

### Step 1 — Build and push the Docker image

The deploy Dockerfile (`Dockerfile.deploy`) will be used. Note that no security information is backed into this image. The security information are built when the container starts.

Then build for AMD64 (OCI Container Instances use x86), tag, and push:

```bash
# Build for AMD64
docker build --platform linux/amd64 -f option_b_fastapi/Dockerfile.deploy -t translate-api:deploy .
ex (no need tag after here) : docker build --platform linux/amd64 -f option_b_fastapi/Dockerfile.deploy -t cdg.ocir.io/frsxwtjslf35/translate-api:8.0.0 .

# Tag for OCIR if needed
# Just fyi here but never use tag latest if you can avoid it (it is a best practise).
docker tag translate-api:deploy <region-key>.ocir.io/<namespace>/translate-api:latest
ex : docker tag translate-api:deploy fra.ocir.io/frsxwtjslf35/translate-api:latest

# Push
docker push <region-key>.ocir.io/<namespace>/translate-api:latest
ex : docker push fra.ocir.io/frsxwtjslf35/translate-api:latest
or ex without latest : docker push cdg.ocir.io/frsxwtjslf35/translate-api:2.0.0
```

### Step 2 — Deploy with Terraform

Go to terraform/option_c_xcontainers and follow the Readme

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

After code changes, rebuild, push, then update the variables of the terraform stack and do an apply again.

## Estimated Costs (Go to Oracle Cloud Estimator to check pricing as here it can be wrong)

| Resource | Spec | ~Monthly (USD) |
|---|---|---|
| Container Instance | 1 OCPU, 2 GB RAM, always-on | ~$27 | [*2 for High Availability]
| Flexible Load Balancer | 10 Mbps minimum | ~$10 |
| GenAI inference (Command A) | per request | ~$0.0015/1K input tokens, ~$0.007/1K output tokens |
| OCIR image storage | | negligible |
| May be API Gateway to add security later 

**Fixed infrastructure: ~$37/month** plus GenAI usage. For light usage (a few hundred translations/day), GenAI adds a few dollars/month. To save costs when not in use, tear down with `terraform destroy` and redeploy when needed.

Note : Option_b_container is DEPRECATED. Do not use.