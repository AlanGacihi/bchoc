#!/usr/bin/env/python3

import hashlib
import struct
import os
import datetime
import argparse
import time

BLOCK_SIZE = struct.calcsize("32s d 16s I 12s 20s 20s I p")
BLOCK_STRUCT = struct.Struct("32s d 16s I 12s 20s 20s I p")

class Block:
    def __init__(self, prev_hash, timestamp, case_id, evidence_id, state, handler, organization, data_length, data):
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.case_id = case_id
        self.evidence_id = evidence_id
        self.state = state
        self.handler = handler
        self.organization = organization
        self.data_length = data_length
        self.data = data

    def pack(self):
        prev_hash = self.prev_hash.encode() if self.prev_hash else b'\x00' * 32
        case_id = self.case_id.encode() if self.case_id else b'\x00' * 16
        timestamp = time.mktime(self.timestamp.timetuple())
        evidence_id = int(self.evidence_id) if self.evidence_id else 0
        state = self.state.encode('utf-8') if self.state else b'\x00' * 20
        handler = self.handler.encode('utf-8') if self.handler else b'\x00' * 20
        organization = self.organization.encode('utf-8') if self.organization else b'\x00' * 20
        data_length = int(self.data_length) if self.data_length else 0
        data = self.data.encode('utf-8') if self.data else b''

        return BLOCK_STRUCT.pack(
            prev_hash, timestamp, case_id, evidence_id,
            state, handler, organization, data_length, data
        )
    
    @classmethod
    def hash(cls, block_data):
        packed_block = BLOCK_STRUCT.pack(
            block_data["prev_hash"].encode() if block_data["prev_hash"] else b'\x00' * 32,
            time.mktime(block_data["timestamp"].timetuple()),
            block_data["case_id"].encode() if block_data["case_id"] else b'\x00' * 16,
            int(block_data["evidence_id"]) if block_data["evidence_id"] else 0,
            block_data["state"].encode('utf-8') if block_data["state"] else b'\x00' * 20,
            block_data["handler"].encode('utf-8') if block_data["handler"] else b'\x00' * 20,
            block_data["organization"].encode('utf-8') if block_data["organization"] else b'\x00' * 20,
            int(block_data["data_length"]) if block_data["evidence_id"] else 0,
            block_data["data"].encode('utf-8') if block_data["data"] else b''
        )
        return hashlib.sha256(packed_block).hexdigest()

    @classmethod
    def unpack(cls, data):
        unpacked_data = BLOCK_STRUCT.unpack(data)
        return {
            "prev_hash": unpacked_data[0].decode().strip('\x00'),
            "timestamp": datetime.datetime.fromtimestamp(int(unpacked_data[1])),
            "case_id": unpacked_data[2].decode().strip('\x00'),
            "evidence_id": unpacked_data[3],
            "state": unpacked_data[4].decode('utf-8').strip('\x00'),
            "handler": unpacked_data[5].decode('utf-8').strip('\x00'),
            "organization": unpacked_data[6].decode('utf-8').strip('\x00'),
            "data_length": unpacked_data[7],
            "data": unpacked_data[8].decode('utf-8').strip('\x00')
        }

def init_blockchain():
    filepath = get_environ()
    if not os.path.exists(filepath):
        # Create an initial block if the file doesn't exist
        initial_block = Block(None, datetime.datetime.utcnow(), None, None, "INITIAL", None, None, 14, "Initial block")
        with open(filepath, 'wb') as file:
            file.write(initial_block.pack())
        print("Blockchain file not found. Created INITIAL block.")
    else:
        print("Blockchain file found with INITIAL block.")
    
    return 0

def add_evidence(case_id, evidence_ids, handler, organization):
    if os.path.exists(get_environ()):
        last_block = get_last_block()
        existing_evidence_ids = get_evidence_ids()
        timestamp = datetime.datetime.utcnow()
        prev_hash = Block.hash(last_block)

        if not case_id:
            print('Error: Case ID not provided')
            return 1

        if not evidence_ids or len(evidence_ids) == 0:
            print('Error: Evidence ID(s) not provided')
            return 1

        print(f"Case: {case_id}")
        for evidence_id in evidence_ids:
            if evidence_id not in existing_evidence_ids:
                add_block(prev_hash, timestamp, case_id, evidence_id, "CHECKEDIN", handler, organization, 0, "")
                print(f"Added item: {evidence_id}")
                print("  Status: CHECKEDIN")
                print(f"  Time of action: {timestamp}")
            else:
                print(f"Error: Evidence ID: {evidence_id} already exists in blockchain.")
                return 1
        return 0
    else:
        print("Blockchain file not found. Run init command first.")
        return 1

def get_environ():
    path = os.environ.get('BCHOC_FILE_PATH')
    if path:
        return path
    else:
        return "./bchoc"

def get_evidence_ids():
    evidence_ids = []
    blockchain = get_blockchain()
    for block in blockchain:
        if block['state'] == "CHECKEDIN":
            evidence_ids.append(str(block['evidence_id']))
    return evidence_ids

def add_block(prev_hash, timestamp, case_id, evidence_id, state, handler, organization, data_length, data):
    block = Block(prev_hash, timestamp, case_id, evidence_id, state, handler, organization, data_length, data)
    with open(get_environ(), 'ab') as file:
        file.write(block.pack())
           
def get_last_block():
    with open(get_environ(), 'rb') as file:
        file.seek(-BLOCK_SIZE, os.SEEK_END)
        return Block.unpack(file.read(BLOCK_SIZE))

def get_blockchain():
    blockchain = []
    with open(get_environ(), 'rb') as file:
        while True:
            data = file.read(BLOCK_SIZE)
            if not data:
                break
            blockchain.append(Block.unpack(data))
    return blockchain

def get_block(evidence_id):
    blocks = []
    
    blockchain = get_blockchain()
    for block in blockchain:
        if block['evidence_id'] == int(evidence_id):
            blocks.append(block)
    
    if len(block) != 0:
        return blocks[-1]
    else:
        return None

def checkout(evidence_id, handler, organization):
    block = get_block(evidence_id)
    if block:
        if block['state'] == 'CHECKEDIN':
            print(f"Case: {block['case_id']}")
            timestamp = datetime.datetime.utcnow()
            last_block = get_last_block()
            add_block(last_block['prev_hash'], timestamp, block['case_id'], evidence_id, "CHECKEDOUT", handler, organization, 0, "")
            print(f"Checked out item: {evidence_id}")
            print("  Status: CHECKEDOUT")
            print(f"  Time of action: {timestamp}")
            return 0
        elif block['state'] == 'CHECKEDOUT':
            print("Error: Cannot check out a checked out item. Must check it in first.")
            return 1
        elif block['state'] == 'RELEASED':
            print("Error: Cannot check in a released item.")
            return 1
    else:
        print(f"Cannot checkout. Evidence ID: {evidence_id} not found in blockchain.")
        return 1


def checkin(item_id, handler, organization):
    block = get_block(item_id)
    if block:
        if block['state'] == 'CHECKEDOUT':
            print(f"Case: {block['case_id']}")
            timestamp = datetime.datetime.utcnow()
            last_block = get_last_block()
            add_block(last_block['prev_hash'], timestamp, block['case_id'], item_id, "CHECKEDIN", handler, organization, 0, "")
            print(f"Checked in item: {item_id}")
            print("  Status: CHECKEDIN")
            print(f"  Time of action: {timestamp}")
            return 0
        elif block['state'] == 'CHECKEDIN':
            print("Error: Cannot check in a checked in item. Must check it out first.")
            return 1
        elif block['state'] == 'RELEASED':
            print("Error: Cannot check in a released item.")
            return 1
    else:
        print(f"Cannot checkin. Evidence ID: {item_id} not found in blockchain.")
        return 1

def show_cases():
    cases = set()
    blockchain = get_blockchain()
    cases = set(block['case_id'] for block in blockchain)

    for case in cases:
        if case:
            print(case)

    return 0

def show_items(case_id):
    blockchain = get_blockchain()
    items = [block for block in blockchain if block['case_id'] == case_id]
    for item in items:
        print(item['evidence_id'])
    
    return 0
    
def show_history(case_id=None, evidence_id=None, num_entries=None):
    blockchain = get_blockchain()
    filtered_blocks = [block for block in blockchain]

    if case_id:
        filtered_blocks = [block for block in filtered_blocks if block['case_id'] == case_id]
    if evidence_id:
        filtered_blocks = [block for block in filtered_blocks if block['evidence_id'] == int(evidence_id)]
    
    if num_entries and filtered_blocks:
        filtered_blocks = filtered_blocks[-int(num_entries):]
      
    for block in filtered_blocks:
        print(f"Case: {block['case_id']}")
        print(f"Item: {block['evidence_id']}")
        print(f"Action: {block['state']}")
        print(f"Time: {block['timestamp']}")
        print()
    
    return 0
    
def remove(evidence_id, reason, owner=None):
    block = get_block(evidence_id)
        
    if block:
        if block['state'] == "CHECKEDIN":
            # Prevent any further action by updating the state to the reason for removal
            if reason in ['DISPOSED', 'DESTROYED', 'RELEASED']:
                if reason == 'RELEASED' and not owner:
                    print("Error: Owner must be provided for RELEASED state.")
                    return 1
                else:
                    last_block = get_last_block()
                    timestamp = datetime.datetime.utcnow()
                    add_block(last_block['prev_hash'], timestamp, block['case_id'], evidence_id, reason, block['handler'], owner, 0, "")
                    print(f"Case: {block['case_id']}")
                    print(f"Removed item: {block['evidence_id']}")
                    print(f"  Status: {reason}")
                    print(f"  Owner info: {owner}")
                    print(f"  Time of action: {timestamp}")
                    return 0
            else:
                print(f"Error: Invalid reason for removal: {reason}")
                return 1
        else:
            print(f"Error: Cannot remove item: {evidence_id}. Item must be checked in first.")
            return 1

def verify():
    blockchain = get_blockchain()

    # Print transactions
    print(f"Transactions in blockchain: {len(blockchain)}")

    try:
        # Check initial block
        if not (len(blockchain[0]['prev_hash']) == 0 \
                and len(blockchain[0]['case_id']) == 0 \
                and blockchain[0]['evidence_id'] == 0 \
                and blockchain[0]['state'] == "INITIAL" \
                and len(blockchain[0]['handler']) == 0 \
                and len(blockchain[0]['organization']) == 0 \
                and blockchain[0]['data_length'] == 14 \
                and blockchain[0]['data'] == "Initial block"
                ):
            print("State of blockchain: ERROR")
            print("Bad block: Initial block does not have null parent.")
            return 1
        
        # Check invalid block after initial
        if blockchain[1]['prev_hash'] != Block.hash(blockchain[0]):
            print("State of blockchain: ERROR")
            print("Bad block: Invalid block after initial block.")
            return 1
        
        # Get a duplicate item
        evidence_ids = []
        
        for block in blockchain:
            if block['state'] == "CHECKEDIN":
                if block['evidence_id'] in evidence_ids:
                    print("State of blockchain: ERROR")
                    print(f"Bad block: {Block.hash(block)}")
                    print('Duplicate item')
                else:
                    evidence_ids.append(block['evidence_id'])

        # Check for duplicate parent
        prev_blocks = []

        for block in blockchain:
            if block['prev_hash'] in prev_blocks:
                print("State of blockchain: ERROR")
                print(f"Bad block: {Block.hash(block)}")
                print(f"Previous block: {block['prev_hash']}")
                print('Two blocks were found with the same parent.')
            else:
                prev_blocks.append(block['prev_hash'])

        # Check for doubles
        state = {}

        for block in blockchain:
            if block['state'] not in ['DISPOSED', 'DESTROYED', 'RELEASED', 'INITIAL', 'CHECKEDIN', 'CHECKEDOUT']:
                print("State of blockchain: ERROR")
                print(f"Bad block: {Block.hash(block)}")
                print('Invalid reason.')
                return 1
            
            if block['state'] in ['DISPOSED', 'DESTROYED', 'RELEASED'] and not block['organization']:
                print("State of blockchain: ERROR")
                print(f"Bad block: {Block.hash(block)}")
                print('Release without owner info')
                return 1
                          
            if block['evidence_id'] in state:
                if state[block['evidence_id']] == "CHECKEDIN" and block['state'] == "CHECKEDIN":
                    print("State of blockchain: ERROR")
                    print(f"Bad block: {Block.hash(block)}")
                    print(f"Item: {block['evidence_id']}")
                    print('Item was checked in twice.')
                    return 1
                elif state[block['evidence_id']] == "CHECKEDOUT" and block['state'] == "CHECKEDOUT":
                    print("State of blockchain: ERROR")
                    print(f"Bad block: {Block.hash(block)}")
                    print(f"Item: {block['evidence_id']}")
                    print('Item was checked out twice.')
                    return 1
                elif state[block['evidence_id']] in ['DISPOSED', 'DESTROYED', 'RELEASED'] and block['state'] in ['DISPOSED', 'DESTROYED', 'RELEASED']:
                    print("State of blockchain: ERROR")
                    print(f"Bad block: {Block.hash(block)}")
                    print(f"Item: {block['evidence_id']}")
                    print('Item was removed twice.')
                    return 1
                elif state[block['evidence_id']] in ['DISPOSED', 'DESTROYED', 'RELEASED'] and block['state'] == "CHECKEDIN":
                    print("State of blockchain: ERROR")
                    print(f"Bad block: {Block.hash(block)}")
                    print(f"Item: {block['evidence_id']}")
                    print('Item checked out or checked in after removal from chain.')
                    return 1
                elif state[block['evidence_id']] == "CHECKEDOUT" and block['state'] in ['DISPOSED', 'DESTROYED', 'RELEASED']:
                    print("State of blockchain: ERROR")
                    print(f"Bad block: {Block.hash(block)}")
                    print(f"Item: {block['evidence_id']}")
                    print('Item checked out or checked in after removal from chain.')
                    return 1
            else: 
                if block['state'] in ['DISPOSED', 'DESTROYED', 'RELEASED']:
                    print("State of blockchain: ERROR")
                    print(f"Bad block: {Block.hash(block)}")
                    print('Item removed before being added.')
                    return 1
                else:
                    state[block['evidence_id']] = block['state']
       
        print("State of blockchain: ERROR")
        return 0
    
    except Exception as e:
        print("An error occurred")
        #print(e)
        return 1

def main():
    parser = argparse.ArgumentParser(description='Blockchain Chain of Custody Program', add_help=False)

    # Define the subparsers
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    add_parser = subparsers.add_parser('add', help='Add items to a case')
    checkout_parser = subparsers.add_parser('checkout', help='Checkout items from a case')
    checkin_parser = subparsers.add_parser('checkin', help='Checkin items to a case')
    show_cases_parser = subparsers.add_parser('showcases', help='Show all cases')
    show_items_parser = subparsers.add_parser('showitems', help='Show items in a case')
    show_history_parser = subparsers.add_parser('showhistory', help='Show history of a case or item')
    remove_parser = subparsers.add_parser('remove', help='Remove items from a case')
    init_parser = subparsers.add_parser('init', help='Initialize the bchoc system')
    verify_parser = subparsers.add_parser('verify', help='Verify the integrity of the bchoc system')

    # Define the arguments for each subparser
    add_parser.add_argument('-c', '--case-id', help='The ID of the case to add items to', required=True)
    add_parser.add_argument('-i', '--item-id', help='The ID of an item to add', action='append', required=True)
    add_parser.add_argument('-h', '--handler', help='The handler who added the items', required=True)
    add_parser.add_argument('-o', '--organization', help='The organization the items belong to', required=True)

    checkout_parser.add_argument('-i', '--item-id', help='The ID of the item to checkout', required=True)
    checkout_parser.add_argument('-h', '--handler', help='The handler who checked out the item', required=True)
    checkout_parser.add_argument('-o', '--organization', help='The organization the item belongs to', required=True)

    checkin_parser.add_argument('-i', '--item-id', help='The ID of the item to checkin', required=True)
    checkin_parser.add_argument('-h', '--handler', help='The handler who checked in the item', required=True)
    checkin_parser.add_argument('-o', '--organization', help='The organization the item belongs to', required=True)

    show_items_parser.add_argument('-c', '--case-id', help='The ID of the case to show items for', required=True)

    show_history_parser.add_argument('-c', '--case-id', help='The ID of the case to show history for')
    show_history_parser.add_argument('-i', '--item-id', help='The ID of the item to show history for')
    show_history_parser.add_argument('-n', '--num-entries', help='The number of history entries to show')

    remove_parser.add_argument('-i', '--item-id', help='The ID of the item to remove', required=True)
    remove_parser.add_argument('-y', '--reason', help='The reason for removing the item', required=True)
    remove_parser.add_argument('-o', '--owner', help='The owner of the item')

    # Parse the arguments
    args = parser.parse_args()

    # Dispatch to the appropriate handler based on the subcommand
    if args.command == 'init':
        return init_blockchain()
    else:
        if os.path.exists(get_environ()):
            if args.command == 'add':
                return add_evidence(args.case_id, args.item_id, args.handler, args.organization)
            elif args.command == 'checkout':
                return checkout(args.item_id, args.handler, args.organization)
            elif args.command == 'checkin':
                return checkin(args.item_id, args.handler, args.organization)
            elif args.command == 'showcases':
                return show_cases()
            elif args.command == 'showitems':
                return show_items(args.case_id)
            elif args.command == 'showhistory':
                return show_history(args.case_id, args.item_id, args.num_entries)
            elif args.command == 'remove':
                return remove(args.item_id, args.reason, args.owner)
            elif args.command == 'verify':
                return verify()
            else:
                print('Invalid command.')
                return 1
        else:
            print('Blockchain file not found. Run init command first.')
            return 1

if __name__ == '__main__':
    main()

