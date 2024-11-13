import sys
import os
import yaml
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common.infradmin_logs

def load_charges(yaml_file):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    return data['charges']

def calculate_transferable_amount(salary, charges):
    total_charges = sum(charges.values())
    transferable_amount = salary - total_charges
    return transferable_amount

def main():
    parser = argparse.ArgumentParser(description='Calculate transferable amount after charges.')
    parser.add_argument('salary', type=float, help='Salary in euros')
    args = parser.parse_args()
    
    common.infradmin_logs.O_LOGGER = common.infradmin_logs.init_logging('Transfer', False)
    yaml_file_path = '/usr/src/app/infradmin/conf/charges.yaml'
    charges = load_charges(yaml_file_path)
    
    salary = args.salary
    transferable_amount = calculate_transferable_amount(salary, charges)
    
    common.infradmin_logs.O_LOGGER.info(f"Salary: {salary} euros")
    common.infradmin_logs.O_LOGGER.info("Charges: ")
    for charge, amount in charges.items():
        common.infradmin_logs.O_LOGGER.info(f"{charge}: {amount} euros")
    common.infradmin_logs.O_LOGGER.info(f"You can transfer {transferable_amount:.2f} euros to another bank account.")
    
if __name__ == "__main__":
    main()
