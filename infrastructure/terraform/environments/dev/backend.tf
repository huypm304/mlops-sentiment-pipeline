# Remote state for CI/CD and team applies. Configure via backend-config in init
# (see .github/workflows/terraform-*.yml and scripts/bootstrap_tf_state.sh).
terraform {
  backend "s3" {}
}
