# Troubleshooting Methodology

> A practical guide to structured technical troubleshooting, covering problem identification, information gathering, reproduction, hypothesis testing, verification, resolution, escalation, and documentation.

## Purpose

Technical troubleshooting is a structured process used to identify the cause of a technical problem and restore normal operation.

A good troubleshooting process avoids random changes and uses evidence to narrow down the possible causes.

## The Troubleshooting Process

### 1. Identify the Problem

Clearly define what is happening.

Ask:

- What is the expected behavior?
- What is the actual behavior?
- When did the problem begin?
- Who is affected?
- Is the issue consistent or intermittent?

### 2. Gather Information

Collect relevant technical information before making changes.

Examples include:

- Error messages
- Screenshots
- Timestamps
- User information
- Browser and operating system
- Device information
- Network information
- Steps to reproduce
- Recent configuration or system changes

### 3. Reproduce the Issue

Try to reproduce the problem using the same or similar conditions.

If the issue can be reproduced, document the exact steps.

If it cannot be reproduced, document what was tested and what the result was.

### 4. Form a Hypothesis

Use the available evidence to identify possible causes.

For example:

If one user cannot access a feature but other users can, possible causes may include:

- User permissions
- Account configuration
- Browser-related issues
- User-specific settings

If many users cannot access the same feature, possible causes may include:

- Application outage
- Deployment problem
- Service dependency
- Network issue

### 5. Test One Change at a Time

Avoid changing multiple variables at the same time.

Make one controlled change, test the result, and document what happened.

This makes it easier to identify which action affected the problem.

### 6. Check the Results

After testing a possible solution, verify whether the expected behavior has returned.

Do not assume that the issue is resolved simply because an error disappeared.

Confirm the complete workflow.

### 7. Resolve or Escalate

If the issue is understood and within the support team's scope, resolve it and document the solution.

If the issue requires another technical team, escalate it with useful evidence.

A good escalation should allow the next team to continue the investigation without starting from the beginning.

## Common Troubleshooting Questions

When investigating an issue, ask:

- What changed?
- When did it start?
- Who is affected?
- Can I reproduce it?
- Does it happen in another browser?
- Does it happen on another device?
- Does another user experience the same problem?
- Is the issue related to permissions?
- Is the issue related to configuration?
- Are there relevant logs?
- Are there relevant API responses?
- Are there recent deployments or changes?

## Example

### Problem

A customer reports that a page is not loading correctly.

### Investigation

1. Confirm the affected URL.
2. Collect the error message and timestamp.
3. Reproduce the issue.
4. Test another browser.
5. Check browser developer tools.
6. Check network requests.
7. Compare the result with another user or environment.
8. Review relevant application logs.
9. Identify whether the problem is user-specific or system-wide.
10. Resolve or escalate based on the evidence.

## Key Principle

Effective troubleshooting is evidence-based.

A useful sequence is:

**Identify → Gather Information → Reproduce → Hypothesize → Test → Verify → Resolve or Escalate → Document**
