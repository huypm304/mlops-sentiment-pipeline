# Step Functions — training pipeline

## Definitions

| File | Use |
|------|-----|
| `training_pipeline.asl.json` | **Compact** graph for thesis figures / cleaner AWS Console screenshots |
| `training_pipeline.full.asl.json` | Full production graph (poll loop, smoke test, wait gate) |

Runtime Terraform (`infra/runtime/main.tf`) points at `training_pipeline.asl.json` by default.

### Compact happy path

```
StartTraining → EvaluateCandidate → CompareToProduction → RegisterCandidate
→ PromoteGate → PromoteModel → DeployModel → NotifyResult → Succeed
```

### Restore full graph

In `infra/runtime/main.tf`, set:

```hcl
definition_file = "${path.module}/../modules/step_functions/training_pipeline.full.asl.json"
```

Then Deploy Runtime again.

### Removed in compact (still described in thesis text / appendix)

- `CheckTrainingStatus` / `WaitForTraining` / `TrainingCompleteGate` (poll SageMaker job)
- `SmokeTestCandidate`

Mock training still returns `Completed` immediately, so poll is unnecessary for demo screenshots.
