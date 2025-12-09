# CAM Phase 9: Deployment Checklist

**Deployment Date:** [FILL IN]  
**Deployed By:** [FILL IN]  
**Status:** ⏳ READY FOR DEPLOYMENT

---

## Pre-Deployment Verification

### Code Quality
- [ ] All Python files compile without syntax errors
- [ ] All imports resolve correctly
- [ ] No hardcoded credentials or test data
- [ ] Logging is appropriate (INFO, WARNING, ERROR levels)
- [ ] Error handling catches and logs all exceptions

### Testing
- [ ] All 14 tests in `test_review_queue.py` pass
- [ ] Test coverage > 90%
- [ ] No failing tests from existing test suite
- [ ] Integration tests pass (if applicable)

### Documentation
- [ ] Quick Reference complete (`CAM_PHASE_9_QUICK_REFERENCE.md`)
- [ ] Operational Guide complete (`CAM_PHASE_9_REVIEW_QUEUE_COMPLETE.md`)
- [ ] Integration Guide complete (`CAM_PHASE_9_INTEGRATION_GUIDE.md`)
- [ ] Status Report complete (`CAM_PHASE_9_STATUS.md`)

### Database
- [ ] Schema changes reviewed (LeadDB extensions)
- [ ] Migration script prepared (if needed)
- [ ] Backup strategy documented
- [ ] No breaking changes to existing models

---

## Staging Environment Deployment

### 1. Deploy Code
```bash
# Copy files to staging
cp aicmo/cam/engine/review_queue.py /staging/aicmo/cam/engine/
cp aicmo/cam/api/review_queue.py /staging/aicmo/cam/api/

# Verify imports
python3 -c "from aicmo.cam.engine.review_queue import *; print('OK')"
```
- [ ] Code deployed to staging
- [ ] No import errors
- [ ] File permissions correct

### 2. Database Setup
```bash
# If using migrations
alembic upgrade head

# Or for fresh database
python3 -c "from aicmo.cam.db_models import *; Base.metadata.create_all(engine)"
```
- [ ] Database schema updated
- [ ] Backup created before schema change
- [ ] Existing data preserved

### 3. API Registration
```python
# In aicmo/cam/api/app.py
from aicmo.cam.api import review_queue

app.register_blueprint(review_queue.bp)
```
- [ ] Review queue blueprint registered
- [ ] Routes appear in Flask app
- [ ] API documentation updated

### 4. Integration Points
Review and test integration with:
```python
# Phase 4-5 Outreach Engine
- [ ] Check lead.requires_human_review before sending
- [ ] Log skipped leads

# Phase 5 Scoring Engine  
- [ ] Flag high-score leads (> 90)
- [ ] Verify flagging works

# Phase 8 Quality Gates
- [ ] Flag on quality violations
- [ ] Test with intentional issues
```

### 5. Smoke Tests (Staging)
```bash
# Start staging server
flask run

# Test API endpoints
curl http://localhost:5000/api/v1/review-queue/stats
curl http://localhost:5000/api/v1/review-queue/tasks

# Expected: 200 OK, empty list or valid JSON
```
- [ ] All endpoints respond
- [ ] Responses are valid JSON
- [ ] Status codes correct (200 for success, 404 for not found)
- [ ] Authentication works

### 6. Load Testing
```bash
# Test with realistic load
ab -n 100 -c 10 http://staging/api/v1/review-queue/tasks
ab -n 50 -c 5 -p data.json -T application/json \
   http://staging/api/v1/review-queue/tasks/1/approve
```
- [ ] API handles 100+ concurrent requests
- [ ] Response time < 500ms p95
- [ ] No memory leaks or database connection issues
- [ ] Error handling works under load

### 7. Security Review
- [ ] All endpoints require login (Flask-Login)
- [ ] No SQL injection vulnerabilities
- [ ] No sensitive data in logs
- [ ] Database transactions are properly committed/rolled back
- [ ] Error messages don't expose internals

### 8. Operator Training (Staging)
- [ ] Select 2-3 operators for staging test
- [ ] Walk through workflow
  - [ ] View review queue
  - [ ] Approve a task
  - [ ] Reject a task
  - [ ] View queue stats
- [ ] Gather feedback
- [ ] Document any issues

---

## Production Environment Deployment

### 1. Pre-Production Backup
```bash
# Backup database
mysqldump -u user -p cam_db > cam_db_backup_$(date +%Y%m%d).sql

# Backup code
git tag phase-9-production-release
git push origin phase-9-production-release
```
- [ ] Database backup created
- [ ] Backup verified (can restore)
- [ ] Git tag created
- [ ] Rollback procedure documented

### 2. Code Deployment
```bash
# Deploy to production
ansible-playbook deploy.yml -e version=phase-9 -e env=production

# Or manual deployment
scp aicmo/cam/engine/review_queue.py prod:/app/aicmo/cam/engine/
scp aicmo/cam/api/review_queue.py prod:/app/aicmo/cam/api/

# Verify
ssh prod "python3 -c 'from aicmo.cam.engine.review_queue import *; print(\"OK\")'"
```
- [ ] Code deployed to all app servers
- [ ] Imports verified on production
- [ ] File permissions correct (readable, not writable by app)

### 3. Database Migration
```bash
# Run migration on production
alembic upgrade head

# Verify schema
mysql -u user -p cam_db -e "DESCRIBE leads;" | grep requires_human_review
```
- [ ] Schema migration completed
- [ ] New fields present on LeadDB
- [ ] Existing data intact
- [ ] Indexes created (if needed)

### 4. Feature Flag (if applicable)
```python
# Optional: Enable gradually
PHASE_9_ENABLED = os.getenv("PHASE_9_ENABLED", "false") == "true"

if PHASE_9_ENABLED:
    app.register_blueprint(review_queue_bp)
```
- [ ] Feature flag set correctly
- [ ] Can disable without code redeploy
- [ ] Monitored for toggles

### 5. Operator Notification
- [ ] Send message to all operators:
  - New review queue feature available
  - How to access (`/dashboard/review-queue`)
  - Quick start guide attached
  - Point of contact for issues
- [ ] Schedule brief training session
- [ ] Provide emergency contact info

### 6. Monitoring Activation
```bash
# Set up alerts
- [ ] Queue size exceeds 100 tasks
- [ ] Oldest task > 24 hours old
- [ ] API error rate > 1%
- [ ] Database connection pool > 80% utilized
```

### 7. Production Smoke Tests
```bash
# Test production endpoints
curl -H "Authorization: Bearer TOKEN" \
  https://production/api/v1/review-queue/stats

# Should return
# {"total_pending": 0, "by_type": {}, "oldest_task_created_at": null}
```
- [ ] All endpoints accessible
- [ ] Authentication required and works
- [ ] Database connectivity OK
- [ ] Logging working

### 8. Phase-In Strategy
```
Day 1: Deploy code, monitor (no automatic flagging yet)
Day 2: Enable scoring integration (auto-flag high scores)
Day 3: Enable quality gate integration (flag on issues)
Day 4: Monitor metrics, gather operator feedback
Day 5: Full production deployment
```
- [ ] Day 1: Code deployed, dormant
- [ ] Day 2: Scoring integration enabled
- [ ] Day 3: Quality gate integration enabled
- [ ] Days 4-5: Full monitoring and feedback

---

## Post-Deployment Verification

### Hour 1 (Immediate)
- [ ] No errors in application logs
- [ ] API endpoints responding
- [ ] No spike in error rate
- [ ] Database queries performing normally

### Hour 4 (After typical morning period)
- [ ] Verify operators can access queue
- [ ] Test manual flagging works
- [ ] Review queue appears empty or populated correctly
- [ ] No database performance degradation

### Day 1 (End of business)
- [ ] Review error logs (should be none)
- [ ] Check queue metrics
  - [ ] Total pending tasks
  - [ ] Average task age
  - [ ] Approval vs reject ratio
- [ ] Gather operator feedback
- [ ] Document any issues

### Day 7 (One week)
- [ ] Compile metrics report
  - [ ] Total leads reviewed
  - [ ] Approval rate
  - [ ] Average review time
  - [ ] False-positive flags (inappropriate reviews)
- [ ] Team retrospective
- [ ] Document lessons learned
- [ ] Plan Phase 10 enhancements

---

## Rollback Plan (If Needed)

### Immediate Rollback (< 5 minutes)
```bash
# 1. Disable review queue blueprint
# In aicmo/cam/api/app.py, comment out:
# app.register_blueprint(review_queue_bp)

# 2. Clear all review flags
mysql -u user -p cam_db -e \
  "UPDATE leads SET requires_human_review=FALSE, review_type=NULL, review_reason=NULL;"

# 3. Restart application
systemctl restart cam-api

# 4. Verify
curl https://production/api/v1/leads/1  # Should work normally
```
- [ ] Blueprint disabled
- [ ] Database reset
- [ ] Application restarted
- [ ] Verified operational

### Full Rollback (< 15 minutes)
```bash
# 1. Revert code to previous version
git checkout HEAD~1 -- aicmo/cam/engine/review_queue.py aicmo/cam/api/review_queue.py

# 2. Remove review queue blueprint registration

# 3. Revert database if needed
mysql < cam_db_backup_20240115.sql

# 4. Restart and verify
systemctl restart cam-api
```
- [ ] Code reverted
- [ ] Database reverted (if schema issue)
- [ ] Tests passing
- [ ] Service online

### Communication Plan
- [ ] Notify operators: "Review queue temporarily disabled"
- [ ] Internal post-mortem
- [ ] Root cause analysis
- [ ] Fix and re-deployment plan

---

## Success Criteria (Post-Deployment)

### Functional ✅
- [ ] Operators can view review queue
- [ ] Operators can approve/reject tasks
- [ ] Review flags prevent outreach
- [ ] API returns correct data
- [ ] Logs show expected activity

### Performance ✅
- [ ] API response time < 200ms (p95)
- [ ] No increased database load
- [ ] Memory usage stable
- [ ] No slow query warnings

### Operational ✅
- [ ] < 5 operator inquiries per week
- [ ] Queue stays < 50 pending tasks
- [ ] SLA compliance > 95% (tasks reviewed < 24h)
- [ ] Approval rate 70-80% (normal range)

### Business ✅
- [ ] Lead quality improved (fewer bad outreach)
- [ ] Operator confidence in automation increased
- [ ] Compliance/legal approves human review layer
- [ ] Ready for Phase 10

---

## Sign-Off

### Deployment Engineer
- [ ] I have reviewed all deployment steps
- [ ] I understand rollback procedure
- [ ] I am available for first 24 hours post-deployment

**Name:** ________________  
**Date:** ________________  
**Signature:** ________________

### Operations Lead
- [ ] Operators trained and ready
- [ ] Monitoring configured
- [ ] Alert recipients notified
- [ ] Runbooks updated

**Name:** ________________  
**Date:** ________________  
**Signature:** ________________

### Engineering Lead (Sign-off)
- [ ] Code review approved
- [ ] Tests passing
- [ ] Documentation complete
- [ ] Ready for production

**Name:** ________________  
**Date:** ________________  
**Signature:** ________________

---

## Post-Deployment Handoff

Document passed to:
- [ ] Operations team
- [ ] Customer success team
- [ ] Product team
- [ ] Engineering team

**Handoff Date:** ________________  
**Received By:** ________________

---

**Deployment Status: ⏳ READY**

Last Updated: 2024-01-15
