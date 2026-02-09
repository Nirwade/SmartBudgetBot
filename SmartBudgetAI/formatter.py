

# SmartBudgetAI/formatter.py

def format_loans(loans):
    if not loans:
        return "You don’t have any active loans 🙂"

    lines = ["Here’s what’s pending:"]
    for loan in loans:
        lines.append(
            f"- {loan['entity']} owes you ${loan['remaining_amount']:.0f}"
        )

    return "\n".join(lines)

