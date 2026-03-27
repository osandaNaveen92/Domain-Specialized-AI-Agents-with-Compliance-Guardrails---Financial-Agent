import pandas as pd

def parse_csv(file_path, source):
    df = pd.read_csv(file_path)

    transactions = []

    for index, row in df.iterrows():
        txn = {
            "transaction_id": f"{source.upper()}_{index}",
            "date": str(row["date"]),
            "amount": float(row["amount"]),
            "description": row["description"],
            "source": source
        }
        transactions.append(txn)

    return transactions