def process_payment(amount):
    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")
    return amount
