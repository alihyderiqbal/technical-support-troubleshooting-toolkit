# Incident Triage

## Purpose

Incident triage is the process of quickly understanding a reported technical issue, determining its impact and urgency, collecting the right information, and deciding the appropriate next action.

The goal is not simply to close a ticket. The goal is to identify the problem accurately, restore service when possible, document the investigation, and escalate with useful technical evidence when necessary.

## 1. Understand the Customer's Issue

Start by identifying exactly what the customer is experiencing.

Ask:

- What is not working?
- What were they trying to do?
- What happened instead?
- When did the issue start?
- Is the issue happening every time or intermittently?
- Is the issue affecting one user or multiple users?
- Can the issue be reproduced?

## 2. Collect Essential Information

Before troubleshooting, collect the information needed to investigate the issue.

Useful information includes:

- Customer or organization name
- Affected user
- Date and time of the issue
- Time zone
- Exact error message
- Screenshot or screen recording
- Steps to reproduce
- Browser and browser version
- Operating system
- Device type
- URL or page where the issue occurred
- Whether the issue affects other users
- Whether the issue occurs in another browser or device
- Recent changes to the account or system

## 3. Determine Impact

Determine how widely the issue is affecting the customer.

Consider:

- One user affected
- Multiple users affected
- One organization affected
- Multiple organizations affected
- One feature affected
- Major functionality unavailable

The broader the impact, the more carefully the incident should be prioritized.

## 4. Check Reproducibility

Try to reproduce the issue when possible.

A useful reproduction process is:

1. Sign in to the appropriate environment.
2. Navigate to the affected feature.
3. Follow the customer's reported steps.
4. Record the result.
5. Compare the expected behavior with the actual behavior.

If the issue cannot be reproduced, document exactly what was tested.

## 5. Investigate Technical Evidence

Depending on the issue, investigate available technical evidence such as:

- Application logs
- Browser developer tools
- Network requests
- API responses
- Database records
- System configuration
- Recent deployments or changes
- Account permissions
- Authentication status
- Email delivery information

Avoid making assumptions before reviewing the available evidence.

## 6. Determine the Next Action

After the initial investigation, decide whether to:

- Resolve the issue
- Provide instructions to the customer
- Continue investigating
- Monitor the issue
- Escalate to another technical team
- Create or update internal documentation

## 7. Escalation

A good escalation should contain enough information for the next technical team to continue the investigation without repeating the entire initial troubleshooting process.

Include:

- Problem summary
- Customer or organization
- Impact
- Exact error
- Time of occurrence
- Steps to reproduce
- Troubleshooting already performed
- Relevant screenshots
- Logs or technical evidence
- Browser/device information
- Expected behavior
- Actual behavior
- Business impact
- Questions that need investigation

## Example Case Summary

**Issue:** User cannot complete a registration payment.

**Impact:** One organization is affected.

**Time:** 2026-09-29 10:30 UTC.

**Expected behavior:** Payment should complete successfully and create the transaction.

**Actual behavior:** Payment fails after the customer submits the payment form.

**Troubleshooting performed:**

- Reproduced the issue.
- Tested in a second browser.
- Confirmed the user has the required permissions.
- Checked the application logs.
- Recorded the error timestamp.
- Collected the relevant error message.

**Next action:** Escalate with the collected evidence for further technical investigation.

## Key Principle

Good technical support follows a structured process:

**Understand → Collect Information → Reproduce → Investigate → Resolve or Escalate → Document**

This approach helps reduce unnecessary back-and-forth and makes technical escalations more effective.
