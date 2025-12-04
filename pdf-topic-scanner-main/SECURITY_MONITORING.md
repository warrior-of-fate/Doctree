# Security & Monitoring Guide

This document outlines security best practices and monitoring strategies for the pdf-topic-scanner project.

---

## Security Features Implemented

### 1. **Request Size Validation**
- Maximum file upload size: **500MB** (configurable)
- Enforced at middleware level in FastAPI
- Returns HTTP 413 (Payload Too Large) for oversized files
- Log entries for all rejected uploads

### 2. **Rate Limiting**
- **10 requests per minute per client IP** on `/extract` endpoint
- Prevents abuse and brute-force attacks
- Rate limiter: `slowapi` library (async-compatible)
- Returns HTTP 429 (Too Many Requests) when limit exceeded

### 3. **Input Validation**
- File type validation: Only `.pdf` files accepted
- Filename sanitization
- Content-type checks

### 4. **Security Headers**
The following security headers are automatically added to all responses:
```
X-Content-Type-Options: nosniff          # Prevents MIME-type sniffing
X-Frame-Options: DENY                    # Prevents clickjacking
X-XSS-Protection: 1; mode=block          # XSS protection
Strict-Transport-Security: ...           # HTTPS enforcement
```

### 5. **CORS Configuration**
- **Development:** All origins allowed (`*`)
- **Production:** Configure via `ALLOWED_ORIGINS` environment variable
- Allowed methods: `GET`, `POST` (others blocked)

### 6. **Structured Logging**
All requests and errors are logged with:
- Timestamp
- Request ID (from `X-Request-ID` header)
- Operation (upload, processing, cleanup)
- Duration and metrics
- Error stack traces for debugging

### 7. **File Handling**
- Temporary files stored in system temp directory
- Files automatically deleted after processing
- Error handling ensures cleanup even on failure

---

## Environment Variables for Security

```bash
# CORS configuration (comma-separated origins)
ALLOWED_ORIGINS="https://example.com,https://api.example.com"

# Rate limiting (configured in code, can be extended)
# RATE_LIMIT="10/minute"  # Not yet exposed as env var

# Logging level
LOG_LEVEL="INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# File upload size (bytes)
MAX_FILE_SIZE=524288000  # 500MB
```

### Setting Environment Variables

**Local Development (.env file):**
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
LOG_LEVEL=DEBUG
```

**Docker Compose:**
```yaml
services:
  backend:
    environment:
      - ALLOWED_ORIGINS=http://frontend:3000
      - LOG_LEVEL=INFO
```

**Render/Railway:**
In service dashboard → Environment Variables:
```
ALLOWED_ORIGINS=https://your-frontend.vercel.app
LOG_LEVEL=INFO
```

---

## Monitoring & Observability

### 1. **Health Check Endpoint**
```bash
curl http://localhost:8000/health
```
Response:
```json
{"status": "ok", "version": "0.1.0"}
```

Use this endpoint with:
- Load balancer health checks
- Kubernetes liveness probes
- Uptime monitoring services (UptimeRobot, Pingdom)

### 2. **Structured Logs**
Logs are emitted in a consistent format:
```
2025-12-05 10:30:15,123 - __main__ - INFO - [abc-123] Upload started: document.pdf
2025-12-05 10:30:17,456 - __main__ - INFO - [abc-123] Successfully processed PDF in 2.33s. Pages: 5, Blocks: 42
```

**Log Aggregation Setup** (Recommended for Production):
- **ELK Stack:** Elasticsearch + Logstash + Kibana
- **Datadog:** Agent-based log collection and alerting
- **CloudWatch:** AWS native logging
- **Papertrail:** Simple log management
- **Sentry:** Error tracking and alerting

### 3. **Metrics to Monitor**

| Metric | Ideal Range | Warning | Critical |
|--------|-----------|---------|----------|
| API Response Time (P95) | <2s | >5s | >10s |
| Error Rate | <0.1% | >1% | >5% |
| Rate Limit Hits | <1% | >5% | >10% |
| Request Volume | Variable | Spike >2x normal | Spike >5x normal |
| Uptime | >99.95% | <99% | <95% |
| Disk Usage | <50% | >70% | >90% |
| Memory Usage | <60% | >75% | >85% |

### 4. **Alerting Rules**

**Critical (Immediate Action Required):**
- API down or returning 5xx errors >5%
- Response time (P95) > 30 seconds
- Error rate > 10%

**Warning (Monitor & Investigate):**
- Response time (P95) > 5 seconds
- Rate limit hit rate > 5%
- Error rate > 1%
- Disk usage > 80%

---

## Deployment Security Checklist

- [ ] **HTTPS/TLS:** Ensure all endpoints use HTTPS (automatic on Vercel/Render/Railway)
- [ ] **CORS:** Restrict `ALLOWED_ORIGINS` to your frontend domain only (not `*` in production)
- [ ] **Rate Limiting:** Verify rate limiting is active and set appropriately
- [ ] **Logging:** Ensure logs are being collected and aggregated
- [ ] **Secrets Management:** Never commit `.env` files; use platform-provided secret management
- [ ] **Dependency Scanning:** Use `pip audit` to check for vulnerable packages
- [ ] **API Documentation:** Secure Swagger UI (`/docs`) with authentication in production
- [ ] **File Permissions:** Ensure temp directory is writable but not world-accessible
- [ ] **Backups:** Set up automated backups if using databases
- [ ] **Monitoring:** Configure health checks and alerting rules
- [ ] **Incident Response:** Document procedures for handling security incidents

---

## Securing the API

### 1. **Disable Swagger UI in Production**
```python
app = FastAPI(docs_url=None, redoc_url=None)  # Disables /docs and /redoc
```

### 2. **Add Authentication** (Example: API Key)
```python
from fastapi import Header, HTTPException

@app.post("/extract")
async def extract_hierarchy(
    api_key: str = Header(None),
    file: UploadFile = File(...),
):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    # ... rest of endpoint
```

### 3. **Add HTTPS Redirect**
```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
app.add_middleware(HTTPSRedirectMiddleware)
```

### 4. **Request Signing** (Optional)
For high-security scenarios, sign requests using HMAC:
```python
import hmac
import hashlib

def verify_signature(request_body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), request_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)
```

---

## Dependency Management

### Keeping Dependencies Secure
```bash
# Check for vulnerabilities
pip install pip-audit
pip-audit

# Update dependencies
pip install --upgrade -r requirements.txt

# Generate lock file (recommended for reproducibility)
pip freeze > requirements.lock
```

### Automated Dependency Scanning
Use Dependabot (GitHub) or Snyk for automated security updates:
- Automatic PR creation for security patches
- Integrates with CI/CD for testing before merge

---

## Error Handling & Logging Examples

### Successful Request
```
[req-uuid-123] Upload started: budget-report.pdf
[req-uuid-123] Parsed 124 blocks
[req-uuid-123] Successfully processed PDF in 1.45s. Pages: 8, Blocks: 124
```

### Rate Limited Request
```
[req-uuid-456] Rate limit exceeded: 11/minute (max 10)
Response: HTTP 429 - "Too many requests. Please try again later."
```

### Invalid File Type
```
[req-uuid-789] Invalid file type: report.xlsx
Response: HTTP 400 - "Only PDF files are accepted"
```

### File Too Large
```
[req-uuid-abc] Upload rejected: file size 750.5MB exceeds limit 500.0MB
Response: HTTP 413 - "File too large. Max size is 500MB"
```

### Processing Error
```
[req-uuid-def] Processing PDF: document.pdf
[req-uuid-def] Error processing PDF after 2.34s: PDF parsing failed
Response: HTTP 500 - "Error processing PDF. Please try again."
```

---

## Monitoring in Production

### Recommended Setup
1. **Uptime Monitoring:** UptimeRobot or Pingdom
   - Health check every 5 minutes
   - Alert on 2+ consecutive failures

2. **Log Aggregation:** ELK Stack, Datadog, or Papertrail
   - Centralize all logs from backend
   - Set up dashboards for response times and errors

3. **Error Tracking:** Sentry
   - Automatic error detection and alerting
   - Stack trace preservation for debugging

4. **Performance Monitoring:** Prometheus + Grafana
   - Collect metrics from backend
   - Create dashboards for request rates, latencies, error rates

### Example Grafana Dashboard
```json
{
  "dashboard": {
    "title": "DocTree.AI Backend Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{"expr": "rate(http_requests_total[5m])"}]
      },
      {
        "title": "Response Time (P95)",
        "targets": [{"expr": "histogram_quantile(0.95, http_request_duration_seconds)"}]
      },
      {
        "title": "Error Rate",
        "targets": [{"expr": "rate(http_requests_total{status=~'5..'}[5m])"}]
      }
    ]
  }
}
```

---

## Incident Response

### If Breach/Attack is Suspected
1. **Isolate:** Take affected service offline or restrict traffic
2. **Investigate:** Check logs for unauthorized access or data exfiltration
3. **Notify:** Inform relevant stakeholders and users
4. **Patch:** Apply security updates immediately
5. **Review:** Conduct post-incident review to prevent recurrence

### Tools for Investigation
- Check application logs for suspicious patterns
- Use `grep` to search for specific requests or errors
- Analyze access logs for unusual IP addresses
- Review rate limit hit logs for attack patterns

---

## Security Best Practices Summary

✅ **Do:**
- Keep dependencies up-to-date
- Use HTTPS/TLS everywhere
- Implement rate limiting
- Log security-relevant events
- Validate all inputs
- Use environment variables for secrets
- Perform regular security audits

❌ **Don't:**
- Commit secrets to git
- Disable security headers
- Allow unrestricted CORS in production
- Log sensitive data (passwords, API keys, PII)
- Ignore security warnings in dependencies
- Use default credentials
- Expose error details to clients in production

---

## Additional Resources

- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **FastAPI Security:** https://fastapi.tiangolo.com/tutorial/security/
- **Slowapi Rate Limiting:** https://github.com/laurentS/slowapi
- **Sentry Error Tracking:** https://sentry.io/
- **Snyk Dependency Scanning:** https://snyk.io/
