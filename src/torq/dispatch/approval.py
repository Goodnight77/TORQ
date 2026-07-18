"""Supervisor approval queue.

Human-in-the-loop approval step (AgentRQ pattern): queue generated work
orders for one-tap supervisor approval or rejection before dispatch.
"""

# TODO: enqueue work orders pending approval
# TODO: expose approve/reject actions with supervisor identity + reason
# TODO: block dispatch until approved; support timeouts/escalation
