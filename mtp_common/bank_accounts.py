import re


EIGHT_DIGIT = re.compile('[0-9]{8}')
NINE_DIGIT = re.compile('[0-9]{9}')
TEN_DIGIT = re.compile('[0-9]{10}')
ELEVEN_DIGIT = re.compile('[0-9]{11}')
FOURTEEN_DIGIT = re.compile('[0-9]{14}')
N_DIGIT = re.compile('[0-9]+')
NINE_DIGIT_WITH_TRAILING_X = re.compile('[0-9]{9}[0-9Xx]')

ROLL_NUMBER_PATTERNS = {
    '621719': TEN_DIGIT,
    '623045': {'00000000': EIGHT_DIGIT},
    '209778': {'00968773': N_DIGIT},
    '134000': {'00000000': re.compile('[0-9]{3}([A-Za-z] |[A-Za-z]{2})[0-9]{6}[A-Za-z]')},
    '134012': FOURTEEN_DIGIT,
    '134013': FOURTEEN_DIGIT,
    '134014': FOURTEEN_DIGIT,
    '134015': FOURTEEN_DIGIT,
    '134016': FOURTEEN_DIGIT,
    '134017': FOURTEEN_DIGIT,
    '571184': {'53731530': N_DIGIT},
    '571327': {'00000000': re.compile('[0-9]{8,9}')},
    '201722': {'40338346': TEN_DIGIT},
    '609595': '.*',
    '207842': {'70798924': NINE_DIGIT},
    '205377': {'50244961': re.compile('[0-9]{9,11}')},
    '161622': {'11758805': NINE_DIGIT_WITH_TRAILING_X},
    '401903': {'40277061': EIGHT_DIGIT},
    '570055': {'00000000': re.compile('[0-9]{8,9}')},
    '089048': {'70715024': NINE_DIGIT},
    '839207': {'00000000': N_DIGIT},
    '601106': {'13761536': NINE_DIGIT_WITH_TRAILING_X},
    '089072': {'70361591': TEN_DIGIT},
    '151000': {'23114065': NINE_DIGIT},
    '402311': {'01246356': NINE_DIGIT_WITH_TRAILING_X},
    '402419': {'81228218': ELEVEN_DIGIT},
    '234448': {'00004000': NINE_DIGIT},
    '622497': {'00000000': re.compile('[A-Za-z]{2,3}[0-9]{7}[A-Za-z]{3}')},
    '402715': {'12440040': TEN_DIGIT},
    '402801': {'11012258': ELEVEN_DIGIT},
    '300080': {'01781004': NINE_DIGIT},
    '089000': {'70127065': TEN_DIGIT},
    '205562': {'10613185': EIGHT_DIGIT},
    '204908': {'70608386': ELEVEN_DIGIT},
    '609495': TEN_DIGIT,
    '403214': {'10572780': re.compile('[A-Za-z]{3}[0-9]{7}[A-Za-z]{3}')},
    '403427': {'10600717': NINE_DIGIT_WITH_TRAILING_X},
    '402024': {'90614629': TEN_DIGIT},
    '070093': {
        '33333334': re.compile('([0-9]{4}/[0-9]{8,9}|[0-9]{6}-[0-9]{3}|'
                               '[0-9]{2}-[0-9]{6}-[0-9]{5}|'
                               '[0-9]{3}-[0-9]-[0-9]{8}-[0-9]{2})')
    },
    '622874': {'00000000': TEN_DIGIT},
    '235954': {'00000008': re.compile('([A-Za-z0-9]{3}[0-9]{7}[A-Za-z0-9]{3}|[0-9]{9})')},
    '608009': {'96875364': TEN_DIGIT},
    '601621': {'77173163': NINE_DIGIT_WITH_TRAILING_X},
    '201815': {'90653535': N_DIGIT},
    '207405': {'00775991': EIGHT_DIGIT},
    '090000': {'00050005': re.compile('[A-Za-z][0-9]{8}([A-Za-z]{3})?')},
    '830608': {'00255419': re.compile('[0-9]{4}-?[0-9]{5}-?[0-9Xx]')},
    '404303': {'81645846': re.compile('[A-Za-z]{3}[0-9]{7}[A-Za-z]{3}')},
    '309546': {'01464485': NINE_DIGIT},
    '202717': {'70885096': EIGHT_DIGIT},
    '086115': {'00000515': N_DIGIT},
    '404613': {'91066277': N_DIGIT},
    '609204': TEN_DIGIT,
    '622337': TEN_DIGIT,
}


CORRESPONDENCE_ACCOUNTS = {
    # metro bank
    '203253': None,
    # think money
    '161623': None,
    # revolut
    '200353': ['73152596']
}


def is_correspondence_account(sort_code, account_number):
    if sort_code in CORRESPONDENCE_ACCOUNTS:
        account_numbers = CORRESPONDENCE_ACCOUNTS[sort_code]
        return account_numbers is None or account_number in account_numbers
    return False


def roll_number_required(sort_code, account_number):
    if sort_code in ROLL_NUMBER_PATTERNS:
        patterns = ROLL_NUMBER_PATTERNS[sort_code]
        if isinstance(patterns, dict):
            return account_number in patterns
        else:
            return True
    return False


def roll_number_valid_for_account(sort_code, account_number, roll_number):
    if sort_code in ROLL_NUMBER_PATTERNS:
        patterns = ROLL_NUMBER_PATTERNS[sort_code]
        if isinstance(patterns, dict):
            pattern = patterns.get(account_number)
        else:
            pattern = patterns

        if pattern:
            if roll_number:
                m = pattern.match(roll_number)
                if m:
                    return True
    return False
