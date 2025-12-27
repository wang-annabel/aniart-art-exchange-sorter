import pandas as pd
import random

# ==================================================
# CSV Parsing Utilities
# ==================================================

def form_response_to_input(file):
    '''Convert raw Google form response csv to input.csv format'''
    print(file.split('.'))
    if file.split('.')[-1] != 'csv':
        raise TypeError('File extension must be .csv')

    df = pd.read_csv(file)

    # Map the Google Form columns to the input format columns
    # Form columns -> Input columns

    # raises KeyError on missing columns
    input_df = pd.DataFrame({
        'Name': df['Your Name Here:'],
        'Discord': df['Discord handle:'],
        'Email': df['What is your email? (UCI email please!)'],
        'Wishlist': df['Wishlist'],
        'Wishlist Tags': df['Wishlist Tags'],
        'Blacklist Tags': df['Blacklist (optional)'],
        'References': df['References (strongly recommended)'],
        'Previously Assigned': float('nan')  # Empty string for new participants
    })

    # Clean up the data
    # Replace NaN values in Blacklist Tags with empty string
    input_df['Blacklist Tags'] = input_df['Blacklist Tags'].fillna('')

    # Strip whitespace from all string columns
    for col in input_df.columns:
        if input_df[col].dtype == 'object':
            input_df[col] = input_df[col].str.strip()

    return input_df

def commas_to_set(raw):
    if isinstance(raw, float):
        # Empty column is typed as NAN float
        return {}
    return {x.strip() for x in raw.split(',')}

class Artist:
    '''
    Art Exchange CSV format:
    Columns: 
    0. Name
    1. Discord
    2. Email
    3. Wishlist
    4. Wishlist Tags
    5. Blacklist Tags
    6. References
    7. Previously Assigned
    '''
    def __init__(self, row):
        self.name = row.iloc[0]
        self.discord = row.iloc[1]
        self.email = row.iloc[2]
        self.wishlist = row.iloc[3]
        self.wishlist_tags = commas_to_set(row.iloc[4])
        self.blacklist_tags = commas_to_set(row.iloc[5])
        self.references = row.iloc[6]
        self.prevassign = commas_to_set(row.iloc[7])
        self.dataframe = row
    
    def __repr__(self):
        return str(self.__dict__)
    
# ==================================================
# Main Function
# ==================================================

def main():
    NUM_ATTEMPTS = 100
    csvraw = pd.read_csv('input.csv')
    raw = [x[1] for x in csvraw.iterrows()]
    artists = [Artist(x) for x in raw]

    success = False
    final_output = None
    for _ in range(NUM_ATTEMPTS):
        result = run(artists)
        if result['success']:
            final_output = result
            success = True
            break
    
    if success:
        print('SUCCESS')
        assignments = final_output['assignments']
        print_assignments(assignments)
        export_to_csv(assignments)
    else:
        print('FAILED')
        print(f'Could not match after {NUM_ATTEMPTS} attempts')

# ==================================================
# Matching Algorithm
# ==================================================

def run(artists: list[str]):
    assignments = []
    failed = []
    available = artists.copy()

    # Expecting that shuffling list will add enough randomness to assignment
    # process to magically find a fit, increase number of attempts if frequently
    # fails to find match
    #
    # Some datasets simply are not possible to match, in which case, 
    # if the number of attempts is very high and there is still not a match,
    # check the actual wishlists and blacklists to trying and find an opening
    random.shuffle(available)

    for request in artists:
        for i in range(len(available)):
            option = available[i]

            if request.discord == option.discord:
                # Requestor and artist is same person, 
                continue

            # If the REQUESTOR wishlist tags are not in ARTIST blacklist tags
            # AND not already taken, 
            # AND they have not previously drawn for this artist, 
            # assign and drop
            if request.wishlist_tags.isdisjoint(option.blacklist_tags) and request.email not in option.prevassign:
                # The request did not hit anything in the blacklist and haven't drawn for them in the past
                assignments.append((request, option))
                available.pop(i)
                break
        else:
            # If else block executes, iterated over entire option list without
            # finding a match. Put this artist into the failed match list for
            # future reference
            failed.append(request)
    
    output = {
        'success': len(failed) == 0,
        'assignments': assignments,
        'failed': failed,
    }

    return output

# ==================================================
# Print Outs and Export
# ==================================================
            
def print_assignments(assignments):
    print('--- Assignments ---')
    print('Requestor -> Artist')
    print()
    for (req, asgn) in assignments:
        print(f'{req.name} -> {asgn.name}')

'''
    Creates a data frame from a list of records

    Input (python types):
        list_of_records = [
            ('one', '1'),
            ('two', '2'),
            ('three', '3'),
        ]
        column_names = ['text', 'value']

    Output (csv equivalent):
        text,value
        one,1
        two,2
        three,3
'''
def create_dataframe(column_names, list_of_records):
    return pd.DataFrame.from_records(list_of_records, columns=column_names)

# artist, artist tag, requestor, wishlist, references
def export_to_csv(assignments, output_path='output.csv'):
    headers = ['Requestor Name', 'Requestor Discord', 'Assignee Name', 'Assignee Discord', 'Prompt', 'References', 'Intro Message']
    records = []
    for requestor, assignee in assignments:
        intromessage = f'''Hello {assignee.name}! You've been assigned {requestor.name}'s request. Here is the prompt: {requestor.wishlist}. 
        And here are the provided reference pics: {requestor.references}. The first check-in will be on **March 21st**
        Art will be due by **Friday April 4th at Midnight**. Let us know if you have any questions, good luck and have fun! Please respond or react to this message so we know its been received!'''
        r = (requestor.name, requestor.discord, assignee.name, assignee.discord, requestor.wishlist, requestor.references, intromessage)
        records.append(r)

    df = create_dataframe(headers, records)
    df.to_csv(output_path, sep=',', index=False, encoding='utf-8')

# ==================================================
# Execution Guard
# ==================================================

if __name__ == '__main__':
    main()