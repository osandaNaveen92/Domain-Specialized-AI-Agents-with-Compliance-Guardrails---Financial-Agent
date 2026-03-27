from utils.parser import parse_csv
from utils.matcher import match_transactions
from utils.db_utils import save_transactions, save_matches, clear_collections

def main():
    clear_collections()
    
    bank_data = parse_csv("data/sample_bank.csv", "bank")
    gl_data = parse_csv("data/sample_gl.csv", "gl")

    clear_collections()
    save_transactions(bank_data)
    save_transactions(gl_data)

    matched, unmatched_bank, unmatched_gl = match_transactions(bank_data, gl_data)

    save_matches(matched, unmatched_bank, unmatched_gl)

    print("Transactions and matches stored successfully")

if __name__ == "__main__":
    main()