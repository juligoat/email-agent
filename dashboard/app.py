"""
Streamlit dashboard
"""

import time
from typing import Dict, List

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Page configuration
st.set_page_config(page_title="🤖 Email Agent Dashboard", page_icon="🤖", layout="wide")

API_BASE_URL = "http://localhost:8000"


def get_agent_status() -> Dict:
    """Get agent status"""
    try:
        response = requests.get(f"{API_BASE_URL}/agent/status", timeout=5)
        return response.json() if response.status_code == 200 else {}
    except Exception:
        return {}


def get_agent_logs(limit: int = 20) -> List[Dict]:
    """Get agent logs"""
    try:
        response = requests.get(f"{API_BASE_URL}/agent/logs?limit={limit}", timeout=5)
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []


def send_test_email() -> Dict:
    """Send test email"""
    try:
        response = requests.post(f"{API_BASE_URL}/emails/test", timeout=10)
        return response.json() if response.status_code == 200 else {}
    except Exception:
        return {}


def simulate_email(email_data: Dict) -> Dict:
    """Simulate email processing"""
    try:
        response = requests.post(f"{API_BASE_URL}/emails/simulate", json=email_data, timeout=10)
        return response.json() if response.status_code == 200 else {}
    except Exception:
        return {}


def main():
    # Initialize session state
    if "selected_email" not in st.session_state:
        st.session_state.selected_email = None
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False

    # Header
    st.title("🤖 Email Agent Dashboard")
    st.markdown("*Teton tech interview*")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("🎛️ Controls")

        # Auto-refresh
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh

        if auto_refresh:
            time.sleep(30)
            st.rerun()

        # Quick test
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🧪 Quick Test", use_container_width=True):
                with st.spinner("Testing..."):
                    result = send_test_email()
                    if result:
                        st.success("✅ Test completed!")
                        st.json(result)

        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        st.divider()

        # Test scenarios
        st.subheader("📧 Test Scenarios")

        scenario = st.selectbox(
            "Choose scenario:",
            ["General Question", "Current Information Request", "Weather Query", "Custom Email"],
        )

        # Scenario definitions
        scenarios = {
            "General Question": {
                "sender": "user@company.com",
                "subject": "Question about your service",
                "body": "Hi, I'm interested in learning more about your email agent service. What features do you offer and how does the pricing work?",
            },
            "Current Information Request": {
                "sender": "researcher@university.edu",
                "subject": "Research inquiry",
                "body": "I'm researching the latest developments in AI email automation. Can you provide current information about industry trends and recent advances?",
            },
            "Weather Query": {
                "sender": "traveler@email.com",
                "subject": "Weather information needed",
                "body": "I'm planning a trip and need current weather information for San Francisco. Can you help me find the latest forecast?",
            },
        }

        if scenario == "Custom Email":
            sender = st.text_input("From:", "test@example.com")
            subject = st.text_input("Subject:", "Test Email")
            # Using st.text_area with safe height
            body = st.text_area("Body:", "This is a test email.", height=150)
        else:
            selected = scenarios[scenario]
            sender = selected["sender"]
            subject = selected["subject"]
            body = selected["body"]

            st.write(f"**From:** {sender}")
            st.write(f"**Subject:** {subject}")
            st.write("**Body Preview:**")
            # Use st.info instead of text_area to avoid height issues
            st.info(body)

        if st.button("🚀 Send Test Email", use_container_width=True):
            email_data = {"sender": sender, "subject": subject, "body": body, "scenario": scenario}

            with st.spinner("Processing..."):
                result = simulate_email(email_data)
                if result:
                    st.success("✅ Email processed!")
                    st.session_state.selected_email = result
                else:
                    st.error("❌ Processing failed")

    # Main content
    status = get_agent_status()

    # Status metrics
    if status:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            agent_status = status.get("status", "unknown")
            status_emoji = "🟢" if agent_status == "active" else "🔴"
            st.metric("Agent Status", f"{status_emoji} {agent_status.title()}")

        with col2:
            emails_processed = status.get("total_emails_processed", 0)
            st.metric("Emails Processed", f"{emails_processed}")

        with col3:
            gmail_connected = status.get("gmail_connected", False)
            gmail_emoji = "✅" if gmail_connected else "❌"
            st.metric("Gmail Connected", f"{gmail_emoji}")

        with col4:
            active_tools = len(status.get("active_tools", []))
            st.metric("Active Tools", f"{active_tools}")
    else:
        st.error(
            "❌ Unable to connect to agent. Make sure the API is running on http://localhost:8000"
        )

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Agent Overview", "📝 Recent Activity", "🔍 Tool Demo"])

    with tab1:
        if status:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🤖 Agent Information")
                st.write("**Type:** LangChain Enhanced Agent")
                st.write(f"**Status:** {status.get('status', 'Unknown').title()}")
                st.write(
                    f"**Gmail:** {'✅ Connected' if status.get('gmail_connected') else '❌ Disconnected'}"
                )

                if status.get("active_tools"):
                    st.write("**🔧 Available Tools:**")
                    for tool in status.get("active_tools", []):
                        st.write(f"• {tool}")

                # Tool statistics
                if status.get("tool_statistics"):
                    st.write("**📊 Tool Usage:**")
                    stats = status["tool_statistics"]
                    for tool_name, tool_stats in stats.items():
                        if isinstance(tool_stats, dict):
                            usage_count = tool_stats.get("usage_count", 0)
                        else:
                            usage_count = tool_stats  # fallback if tool_stats is just an int
                        st.write(f"• {tool_name}: {usage_count} uses")

            with col2:
                st.subheader("📈 Performance")
                logs = get_agent_logs(50)

                if logs:
                    # Action distribution
                    actions = []
                    for log in logs:
                        if isinstance(log, dict) and isinstance(log.get("decision"), dict):
                            actions.append(log["decision"].get("action_type", "unknown"))

                    if actions:
                        action_counts = pd.Series(actions).value_counts()
                        fig = px.pie(
                            values=action_counts.values,
                            names=action_counts.index,
                            title="Action Distribution",
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No action data available")
                else:
                    st.info("📭 No activity data yet")
                    st.write("**💡 Get Started:**")
                    st.write("• Use test scenarios in sidebar")
                    st.write("• Send real emails from whitelisted addresses")
        else:
            st.error("❌ Unable to connect to agent")

    with tab2:
        st.subheader("📬 Recent Email Processing")
        logs = get_agent_logs(10)

        if logs:
            for i, log in enumerate(logs):
                if not isinstance(log, dict):
                    continue  # skip malformed logs

                with st.expander(
                    f"📧 Email {i+1}: {log.get('email_id', 'Unknown')}", expanded=(i == 0)
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**📨 Email Info:**")
                        st.write(f"• **ID:** `{log.get('email_id', 'N/A')}`")
                        st.write(f"• **Timestamp:** {log.get('timestamp', 'N/A')}")
                        st.write(f"• **Processing Time:** {log.get('execution_time', 0):.2f}s")

                        if log.get("understanding"):
                            st.write("**🧠 Understanding:**")
                            st.info(log["understanding"])

                    with col2:
                        st.write("**🤖 Agent Decision:**")
                        decision = log.get("decision", {})

                        if isinstance(decision, dict):
                            action_type = decision.get("action_type", "N/A")
                            confidence = decision.get("confidence", 0)
                            reasoning = decision.get("reasoning", "N/A")

                            # Color-code confidence
                            conf_color = (
                                "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.5 else "🔴"
                            )

                            st.write(f"• **Action:** `{action_type}`")
                            st.write(f"• **Confidence:** {conf_color} {confidence:.2f}")
                            st.write(f"• **Reasoning:** {reasoning}")

                            # Parameters
                            if decision.get("parameters"):
                                with st.expander("View Parameters"):
                                    st.json(decision["parameters"])

                        st.write("**✅ Execution Result:**")
                        result = log.get("execution_result", "N/A")

                        st.code(str(result), language="text")
        else:
            st.info("📭 No recent activity. Try sending a test email!")

    with tab3:
        st.subheader("🔧 Tool Orchestration Demo")

        st.write("""
        **🤖 How Tool Selection Works:**

        - **General Questions** → Direct reply using existing knowledge
        - **Current Information** → Web search + enhanced reply
        - **Weather/News/Trends** → Web search + contextual response
        - **Agent analyzes email content** to choose appropriate tools
        """)

        if st.session_state.selected_email:
            result = st.session_state.selected_email

            st.write("### 📧 Latest Test Result")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**📨 Input Email:**")
                if "input" in result:
                    inp = result["input"]
                    st.write(f"**From:** {inp.get('sender', 'N/A')}")
                    st.write(f"**Subject:** {inp.get('subject', 'N/A')}")
                    st.write("**Body:**")
                    # FIXED: Use st.code instead of st.text_area
                    st.code(inp.get("body", "N/A"), language="text")

                if "scenario" in result:
                    st.write(f"**🎭 Scenario:** {result['scenario']}")

            with col2:
                st.write("**🤖 Agent Response:**")
                if "result" in result:
                    res = result["result"]
                    action = res.get("action", "N/A")
                    confidence = res.get("confidence", 0)
                    reasoning = res.get("reasoning", "N/A")

                    # Color-code confidence
                    conf_color = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.5 else "🔴"

                    st.write(f"**Action Taken:** `{action}`")
                    st.write(f"**Confidence:** {conf_color} {confidence:.2f}")
                    st.write(f"**Reasoning:** {reasoning}")

                    if res.get("execution_time"):
                        st.write(f"**⏱️ Processing Time:** {res['execution_time']:.2f}s")

                    if res.get("execution_result"):
                        st.write("**📝 Generated Response:**")
                        # FIXED: Use st.code instead of st.text_area
                        st.code(res["execution_result"], language="text")

                    # Tool usage indicator
                    if (
                        "web_search" in action.lower()
                        or "search" in str(res.get("execution_result", "")).lower()
                    ):
                        st.success("🔍 **Tool Used:** Web Search → Enhanced Reply")
                    elif "reply" in action.lower():
                        st.info("💬 **Direct Reply:** Using existing knowledge")
        else:
            st.info("👈 Send a test email from the sidebar to see tool orchestration!")

            # Demo examples
            st.write("### 🎯 Try These Examples:")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**🔍 Web Search Triggers:**")
                st.code(
                    """
• "What's the weather today?"
• "Latest AI developments?"
• "Current news about..."
• "Recent trends in..."
                """,
                    language="text",
                )

            with col2:
                st.write("**💬 Direct Reply Triggers:**")
                st.code(
                    """
• "What are your features?"
• "How does pricing work?"
• "Tell me about your service"
• "What can you do?"
                """,
                    language="text",
                )

        # System info
        st.write("### ℹ️ System Information")
        col1, col2 = st.columns(2)

        with col1:
            st.write("**🔗 Access Points:**")
            st.write("• Dashboard: http://localhost:8501")
            st.write("• API: http://localhost:8000")
            st.write("• Docs: http://localhost:8000/docs")

        with col2:
            st.write("**🛠️ Tech Stack:**")
            st.write("• Agent: LangChain + LangGraph")
            st.write("• Tools: Email Reply + Web Search")
            st.write("• UI: Streamlit Dashboard")


if __name__ == "__main__":
    main()
