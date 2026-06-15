output "state_machine_arn" {
  value = aws_sfn_state_machine.retrain.arn
}

output "state_machine_name" {
  value = aws_sfn_state_machine.retrain.name
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.sfn.name
}
