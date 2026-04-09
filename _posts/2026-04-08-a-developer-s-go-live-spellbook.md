---
layout: post
title: Slaying the Release Dragon - A Practical Pre, Production, and Post-Go-Live Checklist
date: '2026-04-08 00:00:00 +0800'
last_modified_at: '2026-04-09 14:09:00 +0800'
categories: ['Engineering Practices','DevOps']
tags: ['deployment', 'production', 'go-live', 'checklist', 'release-management', 'rollback', 'qa']
slug: a-developer-s-go-live-spellbook
comments: true
image:
  path: /assets/postbg/graph.png
  alt: Go-live checklist banner
---

**Drafts & Dragons** — *Shipping to production always sounds simple until the dragon wakes up.*


In every project, there comes a point where development stops being theory and starts becoming real. Real users. Real data. Real pressure. And that is exactly why go-live is never just about clicking deploy. It is about preparation, control, communication, and recovery.

Over the years, I have learned that a smooth production release is rarely the result of luck. It usually comes from having a disciplined checklist before, during, and after deployment.

This post is my practical go-live playbook for production releases: the pre-activities, live deployment activities, and post-deployment checklist that help reduce risk and keep the team sane.

---

## Why a go-live checklist matters

A deployment checklist is not bureaucracy. It is insurance.

Without one, teams often run into familiar problems:

* Missing environment variables
* Database migrations with hidden side effects
* Broken integrations
* Unclear rollback procedures
* Users not informed of downtime
* “It works on staging” surprises
* No ownership during the deployment window

A checklist gives the team a shared source of truth. It aligns developers, QA, DevOps, support, and stakeholders around what must happen and who is responsible for each step.

In short: checklists turn chaos into process.

---

## Phase 1: Pre-production activities

This phase happens before the actual deployment window. Its goal is simple: remove as many unknowns as possible.

### 1. Confirm scope of release

Before anything else, define exactly what is going live.

Questions to settle:

* What features are included?
* What bug fixes are included?
* Are there deferred items?
* Are there known issues being accepted temporarily?
* Is this a full release, patch release, or emergency hotfix?

If the scope is unclear, production will expose that confusion fast.

### 2. Final code review and branch readiness

Make sure the release branch or production branch is stable.

Checklist:

* All pull requests merged properly
* No unreviewed critical code
* No debug code, test routes, or temporary hacks
* Version/tag prepared
* Changelog prepared if needed

This is also the time to ensure the deployment source is clean and traceable.

### 3. QA and UAT sign-off

Do not rely only on “it passed on my machine.”

Make sure:

* Functional testing is complete
* Regression testing is complete
* Critical user flows are verified
* Bug severity is reviewed
* Business or stakeholder sign-off is documented

For enterprise or client-facing systems, this step matters a lot. A technical release without business acceptance can still fail operationally.

### 4. Database readiness

Database changes are often where dragons hide.

Review:

* New migrations
* Backfill scripts
* Seeders needed in production
* Index creation impact
* Data transformation scripts
* Rollback feasibility

Important questions:

* Are migrations backward-compatible?
* Will any migration lock large tables?
* Is downtime required?
* Is there a backup before migration?

Never treat database deployment as a minor detail.

### 5. Environment and configuration validation

Production issues often come from configuration drift rather than code.

Check:

* Environment variables
* Queue configuration
* Cache drivers
* Mail settings
* Storage permissions
* API keys and secrets
* Cron jobs or scheduled tasks
* Third-party service access
* SSL/domain configuration

A release can be technically correct and still fail because one configuration value is missing.

### 6. Infrastructure and dependency checks

Before go-live, validate the platform itself.

Review:

* Server health
* CPU and memory headroom
* Disk space
* Queue workers running
* Background jobs status
* Load balancer rules
* CDN or caching behavior
* External dependencies availability

If traffic is expected, confirm scaling readiness too.

### 7. Rollback plan

Every deployment should come with a recovery path.

A rollback plan should answer:

* What triggers rollback?
* Who decides rollback?
* How is rollback executed?
* Can code be rolled back safely if migrations already ran?
* What is the fallback if rollback is partial only?

If your rollback plan is “we’ll figure it out,” then you do not have one.

### 8. Communication plan

One of the most overlooked parts of go-live is communication.

Notify:

* Internal stakeholders
* Support team
* QA
* Client or end users if needed
* Operations or infra team

Share:

* Deployment date and time
* Expected downtime or no-downtime status
* Scope of release
* Impacted modules
* Point persons during deployment

A successful deployment is also a communication event.

---

## Phase 2: Production deployment activities

This is the live execution phase. The goal here is controlled, observable deployment.

### 1. Start deployment window with assigned roles

During the deployment, everyone should know their role.

Typical roles:

* Deployment lead
* Backend engineer
* Frontend engineer
* QA verifier
* Infra/DevOps support
* Business or project contact

Avoid having a deployment where everyone is watching but nobody is clearly owning the next move.

### 2. Create backup or restore point

Before touching production:

* Backup database
* Confirm last successful backup
* Create snapshot if applicable
* Verify restore procedure is known

Backups are only useful if restoration is actually possible.

### 3. Enable maintenance controls if needed

Depending on the system:

* Enable maintenance mode
* Restrict write operations
* Pause queue consumers temporarily
* Announce downtime if user-facing

This avoids inconsistent behavior during schema or service transitions.

### 4. Deploy application code

This usually includes:

* Pulling the correct release tag
* Installing dependencies
* Building frontend assets
* Publishing configs if needed
* Clearing and rebuilding caches
* Restarting workers/services

Common commands vary by stack, but the principle is the same: use a repeatable deployment sequence.

### 5. Run database migrations carefully

This should be deliberate, not rushed.

Observe:

* Migration success/failure
* Execution duration
* Schema verification
* Data integrity

For critical systems, watch logs in real time while migrations run.

### 6. Validate critical services immediately

Once deployment completes, do smoke testing right away.

Typical checks:

* Login/authentication
* Dashboard load
* Core CRUD flows
* API health
* Reports generation
* Notifications/email
* File upload/download
* Queues and scheduled jobs

Do not wait for users to tell you what broke.

### 7. Monitor application behavior

Immediately after release, watch:

* Application logs
* Error rates
* Failed jobs
* CPU/memory spikes
* Latency
* Database slow queries
* Third-party integration failures

The first 15–60 minutes after release are where production tells the truth.

---

## Phase 3: Post-deployment activities

A deployment is not complete when the code is live. It is complete when the system is stable and the release is confirmed.

### 1. Perform post-deployment verification

Verify the production system against expected behavior.

Check:

* All major pages load
* Transactions work correctly
* Background jobs process normally
* Reports and exports work
* Data is accurate
* User permissions behave correctly

This is the time to confirm the release did not silently break adjacent features.

### 2. Confirm stakeholder acceptance

Once technical checks pass, confirm with business or client representatives:

* Key workflows are working
* Critical modules are accessible
* Expected fixes are visible
* No blocker remains open

Technical success and business success are not always the same thing.

### 3. Watch for delayed issues

Some issues only appear after normal traffic resumes.

Examples:

* Queue backlog
* Scheduled job failures
* Email delays
* Performance degradation
* Caching inconsistencies
* Permission issues for specific roles

This is why post-release monitoring should continue beyond the first smoke test.

### 4. Close the release formally

A clean release should have closure.

Document:

* Deployment time
* Release version
* Items deployed
* Issues encountered
* Fixes applied during deployment
* Final status
* Pending follow-ups

This helps future audits, retrospectives, and incident reviews.

### 5. Run a release retrospective

Ask:

* What went well?
* What slowed us down?
* What failed unexpectedly?
* What should be automated next time?
* What should be added to the checklist?

Every deployment should improve the next one.

---

## Sample go-live checklist

Here is a simplified checklist you can adapt for your own projects.

### Pre-production checklist

* Release scope confirmed
* PRs merged and reviewed
* QA completed
* UAT/business sign-off received
* Migrations reviewed
* Backup plan confirmed
* Environment variables verified
* Third-party integrations checked
* Rollback steps documented
* Deployment schedule communicated
* Deployment team assigned
* Monitoring/log access ready

### Production deployment checklist

* Deployment window started
* Backup/snapshot created
* Maintenance mode enabled if needed
* Correct release tag deployed
* Dependencies installed
* Assets built and published
* Config/cache cleared and rebuilt
* Queue workers restarted
* Migrations executed
* Smoke test completed
* Logs monitored
* Critical flows verified

### Post-deployment checklist

* User login verified
* Main dashboards verified
* Core transactions verified
* Reports/exports verified
* Email/notifications verified
* Queues and cron jobs verified
* Error logs reviewed
* Stakeholders informed of successful release
* Release notes updated
* Follow-up issues documented
* Retrospective scheduled

---

## Lessons from real deployments

Every team eventually learns the same truth: production is less about heroics and more about discipline.

The best deployments are not the ones where engineers save the day at the last minute. The best deployments are the quiet ones. The ones where everyone knew the plan, the checklist was followed, risks were known, and rollback was ready even if it was never needed.

That is what maturity looks like in software delivery.

Not magic. Not luck. Just solid process.

---

## Final thoughts

For teams building internal tools, SaaS platforms, client systems, or enterprise applications, a deployment checklist is one of the simplest safeguards against preventable production issues.

The goal is not perfection on day one. The goal is consistency. Start with a practical checklist, review it after each release, and let every incident, miss, or near miss improve the process. Over time, those small refinements become the difference between reactive deployments and reliable delivery.

That is how you stop fighting the same deployment dragon twice.

After all, while midnight heroics might sound impressive in retrospect, stable and uneventful releases are usually the greater achievement.

I would love to hear your perspective. What has your team added to its deployment checklist over time? Share your thoughts, lessons, or release-day stories in the comments.

---
