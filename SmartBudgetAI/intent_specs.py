# SmartBudgetAI/intent_specs.py

INTENT_SPECS = {
    "loan_given": {
        "required": ["entity", "amount"],
        "keywords": [
            "lent",
            "loaned",
            "gave"
        ]
    },

    "loan_received": {
        "required": ["entity", "amount"],
        "keywords": [
            "returned",
            "paid back",
            "repaid"
        ]
    },

    "query_debts": {
        "required": [],
        "keywords": [
            "who owes",
            "owes me",
            "owes me money",
            "my debts",
            "my loans",
            "outstanding",
            "pending",
            "debts"
        ]
    }
}
