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

def add_charge(yaml_file, charge, amount):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    data['charges'][charge] = amount
    with open(yaml_file, 'w') as file:
        yaml.dump(data, file)

def remove_charge(yaml_file, charge):
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
    del data['charges'][charge]
    with open(yaml_file, 'w') as file:
        yaml.dump(data, file)

def calculate_transferable_amount(salary, charges):
    total_charges = sum(charges.values())
    transferable_amount = salary - total_charges
    return transferable_amount

def main():
    parser = argparse.ArgumentParser(description='Calculate transferable amount after charges.')
    parser.add_argument('salary', type=float, help='Salary in euros')
    args = parser.parse_args()
    salary = args.salary
    common.infradmin_logs.O_LOGGER = common.infradmin_logs.init_logging('Transfer', False)
    common.infradmin_logs.O_LOGGER.info(f"Salary: {salary} euros")
    
    yaml_file_path = '/usr/src/app/infradmin/conf/charges.yaml'
    charges = load_charges(yaml_file_path)
    common.infradmin_logs.O_LOGGER.info("Charges: ")
    for charge, amount in charges.items():
        common.infradmin_logs.O_LOGGER.info(f"  {charge}: {amount} euros")
    common.infradmin_logs.O_LOGGER.info("Is there any charge you want to change? (yes/no)")
    answer = input()
    if answer == 'yes':
        common.infradmin_logs.O_LOGGER.info("Do you want to add a new charge, update an existing one or delete an existing one? (add/update/delete)")
        action = input()
        if action == 'add':
            common.infradmin_logs.O_LOGGER.info("Enter the charge name: ")
            charge = input()
            common.infradmin_logs.O_LOGGER.info("Enter the charge amount: ")
            amount = float(input())
            add_charge(yaml_file_path, charge, amount)
        elif action == 'update':
            common.infradmin_logs.O_LOGGER.info("Which charge do you want to update? ")
            for charge in charges.keys():
                common.infradmin_logs.O_LOGGER.info(f"  {charge}")
            choice = input()
            common.infradmin_logs.O_LOGGER.info("Enter the new charge amount: ")
            amount = float(input())
            add_charge(yaml_file_path, choice, amount)
        elif action == 'delete':
            common.infradmin_logs.O_LOGGER.info("Which charge do you want to update? ")
            for charge in charges.keys():
                common.infradmin_logs.O_LOGGER.info(f"  {charge}")
            choice = input()
            remove_charge(yaml_file_path, choice)
        else:
            common.infradmin_logs.O_LOGGER.error("Invalid action")
            sys.exit(1)
        charges = load_charges(yaml_file_path)
        common.infradmin_logs.O_LOGGER.info("Updated charges: ")
        for charge, amount in charges.items():
            common.infradmin_logs.O_LOGGER.info(f"  {charge}: {amount} euros")
    
    
    
    transferable_amount = calculate_transferable_amount(salary, charges)
    
    
    
    common.infradmin_logs.O_LOGGER.info(f"You can transfer {transferable_amount:.2f} euros to another bank account.")
    
if __name__ == "__main__":
    main()
