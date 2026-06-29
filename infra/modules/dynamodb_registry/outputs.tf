output "datasets_table_name" {
  value = aws_dynamodb_table.datasets.name
}

output "datasets_table_arn" {
  value = aws_dynamodb_table.datasets.arn
}

output "training_runs_table_name" {
  value = aws_dynamodb_table.training_runs.name
}

output "training_runs_table_arn" {
  value = aws_dynamodb_table.training_runs.arn
}

output "models_table_name" {
  value = aws_dynamodb_table.models.name
}

output "models_table_arn" {
  value = aws_dynamodb_table.models.arn
}

output "predictions_table_name" {
  value = aws_dynamodb_table.predictions.name
}

output "predictions_table_arn" {
  value = aws_dynamodb_table.predictions.arn
}

output "monitoring_snapshots_table_name" {
  value = aws_dynamodb_table.monitoring_snapshots.name
}

output "monitoring_snapshots_table_arn" {
  value = aws_dynamodb_table.monitoring_snapshots.arn
}

output "approval_requests_table_name" {
  value = aws_dynamodb_table.approval_requests.name
}

output "approval_requests_table_arn" {
  value = aws_dynamodb_table.approval_requests.arn
}

output "review_queue_table_name" {
  value = aws_dynamodb_table.review_queue.name
}

output "review_queue_table_arn" {
  value = aws_dynamodb_table.review_queue.arn
}

output "weekly_reports_table_name" {
  value = aws_dynamodb_table.weekly_reports.name
}

output "weekly_reports_table_arn" {
  value = aws_dynamodb_table.weekly_reports.arn
}

output "all_table_arns" {
  description = "List of all DynamoDB table ARNs for IAM policy attachment."
  value = [
    aws_dynamodb_table.datasets.arn,
    aws_dynamodb_table.training_runs.arn,
    aws_dynamodb_table.models.arn,
    aws_dynamodb_table.predictions.arn,
    aws_dynamodb_table.monitoring_snapshots.arn,
    aws_dynamodb_table.approval_requests.arn,
    aws_dynamodb_table.review_queue.arn,
    aws_dynamodb_table.weekly_reports.arn,
  ]
}
