"""
NEXUS AI Agent with Human-in-the-Loop Approval
Demonstrates LangGraph, policy engines, and idempotent actions.
"""

import uuid
from typing import TypedDict

from langgraph.graph import END, StateGraph


# --- 1. Define the Agent State ---
class AgentState(TypedDict):
    """The state that flows through the LangGraph workflow."""

    user_request: str
    action_type: str | None
    action_details: dict | None
    action_id: str | None
    policy_decision: str | None  # "approve", "reject", "needs_human_approval"
    human_decision: str | None  # "approved", "rejected"
    execution_result: str | None


# --- 2. Define the Tools (Actions) ---


def reallocate_inventory(region: str, percentage: float) -> dict:
    """
    Reallocates inventory to a specific region.
    High-cost action: $100,000 per 100% (so 20% = $20,000).
    """
    cost = percentage * 100000
    return {
        "status": "success",
        "action": "reallocate_inventory",
        "region": region,
        "percentage": percentage,
        "cost": cost,
        "message": f"Reallocated {percentage * 100:.0f}% of inventory to {region} region. Cost: ${cost:,.2f}",
    }


def send_notification(recipient: str, message: str) -> dict:
    """Low-cost action that doesn't require approval."""
    return {
        "status": "success",
        "action": "send_notification",
        "recipient": recipient,
        "message": message,
    }


# --- 3. Define the Policy Engine ---


def policy_engine(action_type: str, action_details: dict) -> str:
    """
    Evaluates whether an action needs human approval based on business rules.
    """
    if action_type == "reallocate_inventory":
        cost = action_details.get("percentage", 0) * 100000
        if cost > 5000:  # Threshold: $5,000
            return "needs_human_approval"
        else:
            return "approve"

    elif action_type == "send_notification":
        return "approve"

    else:
        return "reject"


# --- 4. Define the LangGraph Nodes ---


def parse_request(state: AgentState) -> AgentState:
    """Parse the user's request and determine the action type."""
    request = state["user_request"].lower()
    print(f"\n🧠 [Node 1] Parsing request: '{state['user_request']}'")

    if "reallocate" in request and "inventory" in request:
        region = "North" if "north" in request else "South"
        percentage = 0.20 if "20%" in request else 0.10

        state["action_type"] = "reallocate_inventory"
        state["action_details"] = {"region": region, "percentage": percentage}
        state["action_id"] = str(uuid.uuid4())
        print(f"   ➔ Action: {state['action_type']}")
        print(f"   ➔ Details: {state['action_details']}")
        print(f"   ➔ Action ID: {state['action_id']}")

    elif "notify" in request or "send" in request:
        state["action_type"] = "send_notification"
        state["action_details"] = {
            "recipient": "ops-team",
            "message": "Inventory alert",
        }
        state["action_id"] = str(uuid.uuid4())
        print(f"   ➔ Action: {state['action_type']}")
        print(f"   ➔ Action ID: {state['action_id']}")
    else:
        state["action_type"] = None
        print("   ➔ No actionable intent detected")

    return state


def evaluate_policy(state: AgentState) -> AgentState:
    """Apply the policy engine to determine if approval is needed."""
    print("\n🛡️  [Node 2] Evaluating policy...")
    if state["action_type"] is None:
        state["policy_decision"] = "reject"
        print("   ➔ Decision: REJECT (no valid action)")
    else:
        decision = policy_engine(state["action_type"], state["action_details"])
        state["policy_decision"] = decision
        print(f"   ➔ Decision: {decision.upper().replace('_', ' ')}")
    return state


def wait_for_human_approval(state: AgentState) -> AgentState:
    """INTERRUPT POINT: Pause the workflow and wait for human approval."""
    print("\n⏸️  [Node 3] ⚠️ WAITING FOR HUMAN APPROVAL ⚠️")
    print(f"   Action: {state['action_type']}")
    print(f"   Details: {state['action_details']}")
    print(f"   Action ID: {state['action_id']}")

    user_input = input("\n   👤 Human: Type 'approve' or 'reject': ").strip().lower()

    if user_input == "approve":
        state["human_decision"] = "approved"
        print("   ➔ Human Decision: APPROVED")
    else:
        state["human_decision"] = "rejected"
        print("   ➔ Human Decision: REJECTED")
    return state


def execute_action(state: AgentState) -> AgentState:
    """Execute the action (idempotently)."""
    print("\n⚡ [Node 4] Executing action (idempotently)...")
    print(f"   Action ID: {state['action_id']}")

    if state["action_type"] == "reallocate_inventory":
        result = reallocate_inventory(
            state["action_details"]["region"], state["action_details"]["percentage"]
        )
    elif state["action_type"] == "send_notification":
        result = send_notification(
            state["action_details"]["recipient"], state["action_details"]["message"]
        )
    else:
        result = {"status": "error", "message": "Unknown action type"}

    state["execution_result"] = result["message"]
    print(f"   ➔ Result: {state['execution_result']}")
    return state


def handle_rejection(state: AgentState) -> AgentState:
    """Handle the case where the action was rejected."""
    print("\n❌ [Node 5] Action rejected")
    state["execution_result"] = "Action was rejected and not executed."
    return state


# --- 5. Define the LangGraph Workflow ---


def should_continue(state: AgentState) -> str:
    if state["policy_decision"] == "needs_human_approval":
        return "wait_for_approval"
    elif state["policy_decision"] == "approve":
        return "execute"
    else:
        return "reject"


def check_human_decision(state: AgentState) -> str:
    if state["human_decision"] == "approved":
        return "execute"
    else:
        return "reject"


workflow = StateGraph(AgentState)
workflow.add_node("parse_request", parse_request)
workflow.add_node("evaluate_policy", evaluate_policy)
workflow.add_node("wait_for_approval", wait_for_human_approval)
workflow.add_node("execute_action", execute_action)
workflow.add_node("handle_rejection", handle_rejection)

workflow.set_entry_point("parse_request")
workflow.add_edge("parse_request", "evaluate_policy")
workflow.add_conditional_edges(
    "evaluate_policy",
    should_continue,
    {
        "wait_for_approval": "wait_for_approval",
        "execute": "execute_action",
        "reject": "handle_rejection",
    },
)
workflow.add_conditional_edges(
    "wait_for_approval",
    check_human_decision,
    {"execute": "execute_action", "reject": "handle_rejection"},
)
workflow.add_edge("execute_action", END)
workflow.add_edge("handle_rejection", END)

agent = workflow.compile()

# --- 6. Test the Agent ---

if __name__ == "__main__":
    print("=" * 70)
    print("🎯 NEXUS AI Agent with Human-in-the-Loop")
    print("=" * 70)

    # Test 1: High-cost action (requires approval)
    print("\n[Test 1] Reallocate 20% of inventory to North (cost: $20,000)")
    print("-" * 70)
    result1 = agent.invoke(
        {
            "user_request": "Reallocate 20% of inventory to the North region",
            "action_type": None,
            "action_details": None,
            "action_id": None,
            "policy_decision": None,
            "human_decision": None,
            "execution_result": None,
        }
    )
    print(f"\n✅ Final Result: {result1['execution_result']}")

    # Test 2: Low-cost action (no approval needed)
    print("\n" + "=" * 70)
    print("\n[Test 2] Send notification to ops team (no approval needed)")
    print("-" * 70)
    result2 = agent.invoke(
        {
            "user_request": "Send a notification to the ops team",
            "action_type": None,
            "action_details": None,
            "action_id": None,
            "policy_decision": None,
            "human_decision": None,
            "execution_result": None,
        }
    )
    print(f"\n✅ Final Result: {result2['execution_result']}")

    print("\n" + "=" * 70)
    print("✅ Agent workflow test completed!")
    print("=" * 70)
