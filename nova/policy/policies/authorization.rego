package nova.authz

default allow = {
    "allow": false,
    "reason": "denied by default"
}

allow = {
    "allow": true,
    "reason": "system administrator"
} {
    input.subject == "admin"
}

allow = {
    "allow": true,
    "reason": "read-only access"
} {
    input.action == "read"
    input.resource == "metrics"
}
