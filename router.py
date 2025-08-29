ROUTING_RULES = {
    "Invoice": "Finance Department",
    "Contract": "Legal Department",
    "Report": "Analytics",
    "Purchase Order": "PMO",
    "Email": "Support",
    "Others": "General Admin"
}

def get_routing_suggestion(label):
    return ROUTING_RULES.get(label, "General Admin")
