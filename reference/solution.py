#!/usr/bin/env python3
"""State management agent with global data and metadata.

Lab 2.6 Deliverable: Demonstrates global data for shared configuration
and call metadata for per-call state tracking.
"""

from datetime import datetime
from signalwire_agents import AgentBase, SwaigFunctionResult


class ServiceAgent(AgentBase):
    """Customer service agent with comprehensive state management."""

    # Simulated customer database
    CUSTOMERS = {
        "+15551234567": {"id": "C001", "name": "John Smith", "tier": "gold"},
        "+15559876543": {"id": "C002", "name": "Jane Doe", "tier": "silver"},
        "+15551112222": {"id": "C003", "name": "Bob Wilson", "tier": "bronze"},
    }

    def __init__(self):
        super().__init__(name="service-agent")

        self.prompt_add_section(
            "Role",
            "You are a customer service agent for TechCorp. "
            "Help customers with inquiries and track issues."
        )

        self.prompt_add_section(
            "Process",
            bullets=[
                "Identify the customer by phone number",
                "Create support tickets for issues",
                "Add notes to track conversation details",
                "Provide ticket summary when requested"
            ]
        )

        self.add_language("English", "en-US", "rime.spore")

        self._setup_global_data()
        self._setup_functions()

    def _setup_global_data(self):
        """Set up global data available to all function calls."""
        hour = datetime.now().hour

        self.set_global_data({
            "company_name": "TechCorp",
            "support_email": "support@techcorp.com",
            "support_phone": "1-800-TECH",
            "business_hours": "9 AM to 6 PM EST",
            "is_business_hours": 9 <= hour < 18,
            "greeting": "Good morning" if hour < 12 else (
                "Good afternoon" if hour < 17 else "Good evening"
            )
        })

    def _setup_functions(self):
        """Define SWAIG functions for customer service."""

        @self.tool(
            description="Identify customer by phone number",
            parameters={
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "Customer phone number"
                    }
                },
                "required": ["phone"]
            }
        )
        def identify_customer(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            phone = args.get("phone", "")
            customer = self.CUSTOMERS.get(phone)

            if customer:
                global_data = self.get_global_data()
                greeting = global_data.get("greeting", "Hello")

                return (
                    SwaigFunctionResult(
                        f"{greeting}, {customer['name']}! "
                        f"I see you're a {customer['tier']} member. How can I help?"
                    )
                    .update_global_data({
                        "customer_id": customer["id"],
                        "customer_name": customer["name"],
                        "customer_tier": customer["tier"],
                        "identified": True
                    })
                )

            return SwaigFunctionResult(
                "I don't recognize that number. Could you provide your account ID?"
            )

        @self.tool(description="Get company information")
        def get_company_info(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            global_data = self.get_global_data()
            return SwaigFunctionResult(
                f"You've reached {global_data['company_name']}. "
                f"Our hours are {global_data['business_hours']}. "
                f"Email us at {global_data['support_email']}."
            )

        @self.tool(
            description="Create a support ticket",
            parameters={
                "type": "object",
                "properties": {
                    "issue": {
                        "type": "string",
                        "description": "Description of the issue"
                    }
                },
                "required": ["issue"]
            }
        )
        def create_ticket(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            issue = args.get("issue", "")
            raw_data = raw_data or {}
            global_data = raw_data.get("global_data", {})
            customer_id = global_data.get("customer_id", "UNKNOWN")
            customer_name = global_data.get("customer_name", "Customer")

            # Generate ticket ID
            ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            return (
                SwaigFunctionResult(
                    f"I've created ticket {ticket_id} for you, {customer_name}. "
                    "Is there anything else about this issue?"
                )
                .update_global_data({
                    "ticket_id": ticket_id,
                    "ticket_issue": issue,
                    "ticket_notes": [],
                    "ticket_created": datetime.now().isoformat()
                })
            )

        @self.tool(
            description="Add a note to the current ticket",
            parameters={
                "type": "object",
                "properties": {
                    "note": {
                        "type": "string",
                        "description": "Additional information"
                    }
                },
                "required": ["note"]
            }
        )
        def add_ticket_note(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            note = args.get("note", "")
            raw_data = raw_data or {}
            global_data = raw_data.get("global_data", {})
            ticket_id = global_data.get("ticket_id")
            notes = global_data.get("ticket_notes", [])

            if not ticket_id:
                return SwaigFunctionResult(
                    "No ticket found. Would you like me to create one?"
                )

            notes.append({
                "time": datetime.now().isoformat(),
                "content": note
            })

            return (
                SwaigFunctionResult(
                    f"Added note to ticket {ticket_id}. "
                    f"Total notes: {len(notes)}."
                )
                .update_global_data({"ticket_notes": notes})
            )

        @self.tool(description="Get ticket summary")
        def get_ticket_summary(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            raw_data = raw_data or {}
            global_data = raw_data.get("global_data", {})
            ticket_id = global_data.get("ticket_id")
            issue = global_data.get("ticket_issue", "No issue recorded")
            notes = global_data.get("ticket_notes", [])
            customer_name = global_data.get("customer_name", "Customer")

            if not ticket_id:
                return SwaigFunctionResult("No active ticket.")

            return SwaigFunctionResult(
                f"Ticket {ticket_id} for {customer_name}: {issue}. "
                f"{len(notes)} note(s) added."
            )

        @self.tool(
            description="Escalate ticket to supervisor",
            parameters={
                "type": "object",
                "properties": {
                    "reason": {"type": "string"}
                },
                "required": ["reason"]
            }
        )
        def escalate_ticket(args: dict, raw_data: dict = None) -> SwaigFunctionResult:
            reason = args.get("reason", "")
            raw_data = raw_data or {}
            global_data = raw_data.get("global_data", {})
            ticket_id = global_data.get("ticket_id")

            if not ticket_id:
                return SwaigFunctionResult(
                    "No ticket to escalate. Let me create one first."
                )

            return (
                SwaigFunctionResult(
                    f"Ticket {ticket_id} has been escalated. "
                    "A supervisor will contact you within 2 hours."
                )
                .update_global_data({
                    "escalated": True,
                    "escalation_reason": reason,
                    "escalation_time": datetime.now().isoformat()
                })
            )


if __name__ == "__main__":
    agent = ServiceAgent()
    agent.run()
