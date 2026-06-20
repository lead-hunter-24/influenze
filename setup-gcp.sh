#!/usr/bin/env bash
# One-shot setup for GitHub Actions -> Cloud Run via Workload Identity Federation.
# Run ONCE with a gcloud account that is Owner/Editor on the target project.
#
#   gcloud auth login            # use the account that owns silken-bastion-499817-m0
#   bash setup-gcp.sh
#
# It creates: required APIs, a deployer service account, a WIF pool+provider
# scoped to your GitHub repo, the IAM bindings, and a Secret Manager secret for
# the Anthropic key. Then it sets the GitHub Actions secrets via the `gh` CLI.
set -euo pipefail

# ---- EDIT THESE ----
PROJECT_ID="silken-bastion-499817-m0"
REGION="us-central1"
GH_REPO="lead-hunter-24/influenze"          # owner/repo
SERVICE_ACCOUNT="yt-insights-deployer"
POOL="github-pool"
PROVIDER="github-provider"
# Your Anthropic key (or export ANTHROPIC_API_KEY before running)
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-PUT_YOUR_ANTHROPIC_KEY_HERE}"
# --------------------

echo ">> Using project $PROJECT_ID"
gcloud config set project "$PROJECT_ID"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
SA_EMAIL="${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

echo ">> Enabling APIs"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  iamcredentials.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com

echo ">> Creating deployer service account (idempotent)"
gcloud iam service-accounts create "$SERVICE_ACCOUNT" \
  --display-name="YT Insights GitHub deployer" 2>/dev/null || true

echo ">> Granting roles to $SA_EMAIL"
for role in roles/run.admin roles/cloudbuild.builds.editor \
            roles/artifactregistry.admin roles/storage.admin \
            roles/secretmanager.secretAccessor roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_EMAIL}" --role="$role" --condition=None -q >/dev/null
done

echo ">> Creating Anthropic secret in Secret Manager"
if ! gcloud secrets describe anthropic-api-key >/dev/null 2>&1; then
  printf "%s" "$ANTHROPIC_API_KEY" | gcloud secrets create anthropic-api-key --data-file=-
else
  printf "%s" "$ANTHROPIC_API_KEY" | gcloud secrets versions add anthropic-api-key --data-file=-
fi

echo ">> Creating Workload Identity pool + provider"
gcloud iam workload-identity-pools create "$POOL" \
  --location=global --display-name="GitHub Actions pool" 2>/dev/null || true

gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
  --location=global --workload-identity-pool="$POOL" \
  --display-name="GitHub provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='${GH_REPO}'" \
  --issuer-uri="https://token.actions.githubusercontent.com" 2>/dev/null || true

WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}"

echo ">> Allowing the GitHub repo to impersonate the service account"
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${GH_REPO}" -q >/dev/null

echo ">> Setting GitHub Actions secrets (requires gh auth)"
gh secret set GCP_PROJECT_ID      --repo "$GH_REPO" --body "$PROJECT_ID"
gh secret set WIF_PROVIDER        --repo "$GH_REPO" --body "$WIF_PROVIDER"
gh secret set WIF_SERVICE_ACCOUNT --repo "$GH_REPO" --body "$SA_EMAIL"

echo
echo "DONE. Values:"
echo "  GCP_PROJECT_ID      = $PROJECT_ID"
echo "  WIF_PROVIDER        = $WIF_PROVIDER"
echo "  WIF_SERVICE_ACCOUNT = $SA_EMAIL"
echo
echo "Push to main (or run the workflow manually) to trigger the first deploy."
