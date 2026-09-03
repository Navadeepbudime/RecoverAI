# API

Base URL: `http://localhost:5000/api`

## Health

`GET /health`

Returns demo mode, AI provider status, and Razorpay configuration status.

## Metrics

`GET /metrics`

Returns revenue at risk, potentially recoverable revenue, recovered revenue, recovery rate, failed payment count, active cases, successful recoveries, and stopped/escalated cases.

## Cases

`GET /cases`

`GET /cases/<case_id>`

`POST /cases/<case_id>/process`

Case detail includes customer, payment, AI explanation, policy decision, executed action, outcome, and timeline.

## Policy

`GET /policy`

`PUT /policy`

Supported fields: `max_automatic_retries`, `retry_delay_minutes`, `high_value_threshold`, `escalation_threshold`, `repeated_failure_limit`, and `auto_retry_enabled`.

## Simulator

`POST /simulate`

Runs deterministic expected recovery calculations over the current dataset.

## Razorpay Webhook

`POST /webhooks/razorpay`

Verifies `X-Razorpay-Signature` when `RAZORPAY_WEBHOOK_SECRET` is set. In demo mode it can accept unsigned events.
