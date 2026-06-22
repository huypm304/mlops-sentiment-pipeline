output "lambda_role_arn" {
  value = aws_iam_role.lambda.arn
}

output "lambda_role_name" {
  value = aws_iam_role.lambda.name
}

output "step_functions_role_arn" {
  value = aws_iam_role.step_functions.arn
}

output "step_functions_role_name" {
  value = aws_iam_role.step_functions.name
}

output "sagemaker_role_arn" {
  value = aws_iam_role.sagemaker.arn
}

output "sagemaker_role_name" {
  value = aws_iam_role.sagemaker.name
}
