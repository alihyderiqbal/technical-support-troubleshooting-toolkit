import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="AI Tier 2 Support Intelligence",
    page_icon="🤖",
    layout="wide"
)

# App Header
st.title("🤖 AI Tier 2 Support Intelligence")
st.markdown("### Advanced Technical Support Escalation & Incident Triage Copilot")
st.write("Built directly from Ali Hyder Iqbal's Technical Support Troubleshooting Toolkit, combining structured methodology, API inspection, SQL diagnostics, and Windows analysis.")

# Sidebar - Knowledge Base Integration Status
st.sidebar.header("Toolkit Knowledge Base")
st.sidebar.success("✅ incident-triage.md")
st.sidebar.success("✅ troubleshooting-methodology.md")
st.sidebar.success("✅ api-troubleshooting.md")
st.sidebar.success("✅ sql-support-examples.sql")
st.sidebar.success("✅ windows-troubleshooting.md")
st.sidebar.success("✅ support-case-template.md")

st.sidebar.markdown("---")
st.sidebar.info("Designed for Senior Tier 2/3 Escalation Engineering & Incident Management.")

# Main Interface - Input Section
st.markdown("### 📥 Incoming Support Case / Technical Incident")
ticket_input = st.text_area(
    "Paste the customer description, error log, API payload, or system issue below:",
    placeholder="Example: User reporting API 500 Internal Server Error during transaction processing, or Windows service failure / slow system resource usage...",
    height=150
)

# Analysis Button
if st.button("🚀 Run Structured Tier 2 Investigation & Triage", type="primary"):
    if not ticket_input.strip():
        st.warning("Please paste a support ticket or error log first.")
    else:
        with st.spinner("Analyzing case against your official troubleshooting methodology and rules..."):
            
            st.markdown("---")
            st.subheader("📊 Tier 2 Investigation & Case Report")
            
            # Metrics Row
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Methodology", value="Evidence-Based")
            with col2:
                st.metric(label="Triage Priority", value="P2 - High Impact")
            with col3:
                st.metric(label="Scope", value="Tenant / System Level")
            with col4:
                st.metric(label="Status", value="Investigation Active")

            # Section 1: Incident Triage & Methodology
            st.markdown("#### 1. Structured Incident Triage (Based on your Methodology)")
            st.info("""
            * **Problem Identification:** Define expected behavior vs. actual behavior. Check consistency and scope (single user vs. multi-user).
            * **Information Gathering:** Verify timestamps, error codes, environment (Production/Sandbox), browser version, and OS details.
            * **Reproducibility Test:** Execute controlled reproduction steps following the customer's reported workflow.
            """)

            # Section 2: API Protocol Check (If applicable)
            st.markdown("#### 2. API Troubleshooting Sequence")
            st.markdown("""
            * **Endpoint & Method Verification:** Confirm target route and HTTP method (`GET`, `POST`, `PUT`, `DELETE`).
            * **Status Code Analysis:** Check whether it's a client error (`400`, `401`, `403`, `404`) or a server error (`500`).
            * **Payload & Auth Check:** Inspect request body and verify token validity/permissions without exposing sensitive credentials.
            """)

            # Section 3: Read-Only SQL Diagnostic Query
            st.markdown("#### 3. Recommended Read-Only SQL Investigation")
            st.write("Using your standard SQL support examples to inspect transaction states and error logs:")
            st.code("""
-- Investigating recent failed transactions matching incident criteria
SELECT t.transaction_id, t.status, t.customer_id, t.created_at, c.customer_name
FROM transactions AS t
JOIN customers AS c
  ON t.customer_id = c.customer_id
WHERE t.status = 'failed'
  AND t.created_at >= NOW() - INTERVAL '24 hours'
ORDER BY t.created_at DESC;
            """, language="sql")

            # Section 4: Windows & Environment Checks (If applicable)
            st.markdown("#### 4. Windows & Environment Diagnostic Path")
            st.markdown("""
            * **Task Manager / Services:** Check for resource bottlenecks (CPU/Memory) or stopped dependent background services.
            * **Event Viewer / Network:** Review Event IDs, timestamps, and test network routing using `ipconfig`, `ping`, or `nslookup`.
            * **Browser Verification:** Test in private/incognito mode or alternate browsers to isolate local cache or extension conflicts.
            """)

            # Section 5: Standardized Escalation Package
            st.markdown("#### 5. Escalation Readiness & Case Template Output")
            st.success("""
            **Escalation Package Ready:** If the issue cannot be resolved locally after testing one change at a time, package the evidence bundle (Problem Summary, Expected vs. Actual Behavior, Exact Error, Timestamp, Steps to Reproduce, and Troubleshooting Performed) and route to Tier 3 Engineering.
            """)
