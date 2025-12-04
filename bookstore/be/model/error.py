error_code = {
    401: "authorization fail.",
    402: "invalid field {}",
    403: "invalid page {}",
    404: "invalid page size {}",
    511: "non exist user id {}",
    512: "exist user id {}",
    513: "non exist store id {}",
    514: "exist store id {}",
    515: "non exist book id {}",
    516: "exist book id {}",
    517: "stock level low, book id {}",
    518: "invalid order id {}",
    519: "not sufficient funds, order id {}",
    520: "not found results",
    521: "page overflows, you try to enter page {} but total_pages is {}",
    522: "",
    523: "",
    524: "",
    525: "",
    526: "",
    527: "",
    528: "",
}
def error_over_page(page,total_pages):
    return 521, error_code[521].format(page,total_pages)
def error_not_found_results():
    return 520, error_code[520]

def error_invalid_page_size(page_size):
    return 404, error_code[404].format(page_size)

def error_invalid_page(page):
    return 403, error_code[403].format(page)

def error_invalid_field(field):
    return 402, error_code[402].format(field)

def error_non_exist_user_id(user_id):
    return 511, error_code[511].format(user_id)


def error_exist_user_id(user_id):
    return 512, error_code[512].format(user_id)


def error_non_exist_store_id(store_id):
    return 513, error_code[513].format(store_id)


def error_exist_store_id(store_id):
    return 514, error_code[514].format(store_id)


def error_non_exist_book_id(book_id):
    return 515, error_code[515].format(book_id)


def error_exist_book_id(book_id):
    return 516, error_code[516].format(book_id)


def error_stock_level_low(book_id):
    return 517, error_code[517].format(book_id)


def error_invalid_order_id(order_id):
    return 518, error_code[518].format(order_id)


def error_not_sufficient_funds(order_id):
    return 519, error_code[519].format(order_id)


def error_authorization_fail():
    return 401, error_code[401]


def error_and_message(code, message):
    return code, message
