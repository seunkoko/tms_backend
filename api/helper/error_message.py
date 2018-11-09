#errors

# moov_errors standard
def moov_errors(errors, status_code):
    return {
        'status': 'fail',
        'data': { 'message': errors }
    }, status_code

def not_found_errors(item):
    return moov_errors("{0} does not exist".format(item), 404)
