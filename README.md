# Technical Support Troubleshooting Toolkit

A practical technical support portfolio demonstrating structured incident triage, SaaS troubleshooting, API troubleshooting, SQL investigation, Windows troubleshooting, and technical case documentation.

## Skills Demonstrated

* Incident triage
* Technical troubleshooting
* SaaS support
* API troubleshooting
* SQL investigation
* Windows troubleshooting
* ITSM concepts
* Technical documentation
* Escalation methodology
* Evidence-based problem solving
* AI-assisted support tooling (working prototype, see below)

---

## AI Tier 2 Support Intelligence (prototype)

**Live demo:** https://ai-tier2-support-intelligence.streamlit.app

A working prototype that builds on the toolkit below. It helps a Tier 2 engineer investigate a new case by finding similar evidence and telling the engineer what still has to be verified by a human.

> **Status: prototype / proof of concept.** It demonstrates the workflow and the design thinking. It is not a production system (see Limitations).

### The problem

Tier 2 engineers lose time searching playbooks, documentation and old tickets for something similar to the case in front of them. Generic AI answers can also sound confident while being wrong. This project takes a different approach: **find evidence, show it, and tell the engineer what still has to be verified.**

### What the app does

1. **Takes a ticket, Slack thread or error log** pasted by the engineer.
2. **Searches several sources:**
   * the toolkit files in this repository (read directly from the `.md` and `.sql` files),
   * the public [CivicPlus Help Center](https://www.civicplus.help/) (live, from its public documentation index, no API key needed),
   * past cases saved in the app,
   * optionally, closed tickets from **Zendesk** or **Salesforce**, and messages from **Slack**, when credentials are provided.
3. **Ranks the closest matches** with BM25 keyword ranking and shows an *overlap* percentage and an evidence level (**Strong / Moderate / Weak**). It does **not** claim an accuracy figure. Overlap measures similarity, not correctness.
4. **Lists what the engineer must still find out:** details missing from the ticket (time, exact error, who is affected, steps to reproduce, environment, recent changes) and a verification checklist for that type of issue, based on the playbooks.
5. **Suggests read-only SQL starters** from the toolkit for evidence collection.
6. **Learns from feedback:** the engineer saves the outcome of a case. Cases marked "worked" rank higher next time, "did not help" ranks lower. Emails, phone numbers and keys are removed before anything is saved.
7. **Optional AI draft:** if an Anthropic API key is supplied, Claude writes a short draft using **only** the evidence found, and is told to say when the evidence is not enough.

### Design principles

* **Human in the loop:** the app suggests, the engineer decides and verifies.
* **Honest uncertainty:** weak evidence is labelled weak.
* **Evidence over guessing:** every suggestion points to a source.
* **Privacy by default:** personal data is redacted before saving or sending to an AI model. Credentials stay in session memory and are never written to disk.
* **Read-only investigation:** the SQL examples only read data.

### Tech stack

Python, Streamlit, Requests, BM25 search written in plain Python, Zendesk / Salesforce / Slack REST APIs, Anthropic API (optional).

### Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Optional secrets (on Streamlit Cloud: App settings, then Secrets) so nothing is stored in the repository:

```toml
ANTHROPIC_API_KEY = "..."
ZENDESK_SUBDOMAIN = "..."
ZENDESK_EMAIL = "..."
ZENDESK_TOKEN = "..."
SALESFORCE_INSTANCE = "https://yourorg.my.salesforce.com"
SALESFORCE_TOKEN = "..."
SLACK_BOT_TOKEN = "..."
SLACK_CHANNEL = "C0123456789"
```

### Data safety

This repository contains **no customer data**. Demos should use fictional or public information. Only connect live systems where your organisation's policy and admin allow it.

### Limitations

* No user login or role-based access.
* Saved cases are stored in a simple JSON file, which can be lost when the hosting app restarts. A production system needs a database.
* Search is keyword-based. It does not yet match by meaning (embeddings).
* Live connections use manually supplied tokens rather than an admin-approved OAuth flow.
* The Zendesk, Salesforce and Slack connectors have been tested against simulated responses, not against production accounts.
* No audit logging, monitoring or automated test suite in the repository yet.
* Retrieval quality has not been formally measured.

### Roadmap

* Authentication and per-team permissions
* Database storage with an audit trail
* Semantic (embedding) search alongside keyword search
* Admin-approved OAuth connections
* A test set of past solved cases to measure retrieval quality
* An approval step before any recommended action is applied

---

## Repository Contents

### Incident Triage

[incident-triage.md](https://github.com/alihyderiqbal/technical-support-troubleshooting-toolkit/blob/main/incident-triage.md)

A structured approach to understanding customer issues, collecting information, determining impact, reproducing problems, investigating evidence, and escalating cases.

### Troubleshooting Methodology

[troubleshooting-methodology.md](https://github.com/alihyderiqbal/technical-support-troubleshooting-toolkit/blob/main/troubleshooting-methodology.md)

A systematic troubleshooting process covering problem identification, information gathering, hypothesis testing, verification, resolution, and documentation.

### API Troubleshooting

[api-troubleshooting.md](https://github.com/alihyderiqbal/technical-support-troubleshooting-toolkit/blob/main/api-troubleshooting.md)

Practical examples covering HTTP methods, status codes, authentication, permissions, requests, responses, and API investigation.

### SQL Support Examples

[sql-support-examples.sql](https://github.com/alihyderiqbal/technical-support-troubleshooting-toolkit/blob/main/sql-support-examples.sql)

Read-only SQL examples for investigating transactions, customers, organizations, records, and support-related data.

### Windows Troubleshooting

[windows-troubleshooting.md](https://github.com/alihyderiqbal/technical-support-troubleshooting-toolkit/blob/main/windows-troubleshooting.md)

Common Windows support techniques covering Task Manager, Windows Services, Event Viewer, networking commands, browser troubleshooting, and system investigation.

### Support Case Template

[support-case-template.md](https://github.com/alihyderiqbal/technical-support-troubleshooting-toolkit/blob/main/support-case-template.md)

A structured template for documenting technical issues, troubleshooting steps, technical evidence, resolution, verification, and escalation.

### AI Tier 2 Support Intelligence (application files)

* `app.py`: the Streamlit application
* `requirements.txt`: Python dependencies
* `.streamlit/config.toml`: navy theme

---

## Purpose

This project demonstrates how technical support issues can be approached using a structured, evidence-based troubleshooting process.

The focus is on understanding the problem, gathering relevant information, investigating technical evidence, resolving issues when possible, and providing clear documentation when escalation is required.

## Author

**Ali Hyder Iqbal**

Technical Support Engineer | SaaS & B2B Support | IT Troubleshooting | ITSM | SQL | APIs | Salesforce | Jira | Zendesk

Built with AI coding assistance. Workflow design, requirements and testing by the author.
