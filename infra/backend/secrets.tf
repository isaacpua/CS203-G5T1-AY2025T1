# 1. A single key/value secret for your .env file
# We will populate this manually with 4 keys:
# - DB_URL
# - DB_USERNAME
# - DB_PASSWORD
# - OPENAI_API_KEY
resource "aws_secretsmanager_secret" "backend_env" {
  name        = "${var.project_name}-backend-env"
  description = "Key/value pairs for the backend .env file"
}

# 2. A plain-text secret for token.json
resource "aws_secretsmanager_secret" "mcp_token_json" {
  name        = "${var.project_name}-mcp-token-json"
  description = "Content of the MCP-Server token.json file"
}
