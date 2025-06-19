"""
Vulture whitelist for false positives
"""

# FastAPI endpoints - used by framework via decorators
root
get_agent_status
get_agent_logs
receive_email
update_config
clear_logs

# Pydantic model fields - used by framework for serialization/validation
extra
email_id
tool_name

# Pydantic configuration - required by framework
model_config
Config
validate_groq_api_key
