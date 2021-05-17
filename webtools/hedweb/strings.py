from flask import current_app
from werkzeug import Response
from hed.schema.hed_schema_file import load_schema
from hed.util.error_reporter import get_printable_issue_string
from hed.util.hed_string import HedString
from hed.util.exceptions import HedFileError
from hed.validator.hed_validator import HedValidator
from hedweb.constants import common
from hedweb.web_utils import form_has_option, get_hed_path_from_pull_down, get_hed_schema,\
    generate_response_download_file_from_text, generate_text_response
app_config = current_app.config


def generate_input_from_string_form(request):
    """Gets the validation function input arguments from a request object associated with the validation form.

    Parameters
    ----------
    request: Request object
        A Request object containing user data from the validation form.

    Returns
    -------
    dictionary
        A dictionary containing input arguments for calling the underlying validation function.
    """
    hed_file_path, hed_display_name = get_hed_path_from_pull_down(request)
    hed_string = request.form['hedstring-input']
    if hed_string:
        string_list = [hed_string]
    else:
        raise HedFileError('EmptyHedString', 'Must enter a HED string')
    arguments = {common.COMMAND: '',
                 common.HED_XML_FILE: hed_file_path,
                 common.HED_DISPLAY_NAME: hed_display_name,
                 common.STRING_LIST: string_list}
    if form_has_option(request, common.HED_OPTION, common.HED_OPTION_VALIDATE):
        arguments[common.COMMAND] = common.COMMAND_VALIDATE
    elif form_has_option(request, common.HED_OPTION, common.HED_OPTION_TO_SHORT):
        arguments[common.COMMAND] = common.COMMAND_TO_SHORT
    elif form_has_option(request, common.HED_OPTION, common.HED_OPTION_TO_LONG):
        arguments[common.COMMAND] = common.COMMAND_TO_LONG

    return arguments


def string_process(arguments):
    """Perform the requested action on the HED string.

    Parameters
    ----------
    arguments: dict
        A dictionary with the input arguments from the hedstring form

    Returns
    -------
    Response
        Downloadable response object.
    """
    if common.COMMAND not in arguments:
        raise HedFileError('MissingCommand', 'Command is missing', '')
    if arguments[common.COMMAND] == common.COMMAND_VALIDATE:
        results = string_validate(arguments)
    elif arguments[common.COMMAND] == common.COMMAND_TO_SHORT:
        results = string_convert(arguments)
    elif arguments[common.COMMAND] == common.COMMAND_TO_LONG:
        results = string_convert(arguments)
    else:
        raise HedFileError('UnknownProcessingMethod', 'Select a hedstring processing method', '')
    return results


def string_convert(arguments, hed_schema=None):
    """Converts a hedstring from short to long unless short_to_long is set to False, then long_to_short

    Parameters
    ----------
    arguments: dict
        Dictionary containing standard input form arguments
    hed_schema: HedSchema object

    Returns
    -------
    dict
        A dictionary with string_results as the key
    """

    if not hed_schema:
        hed_schema = load_schema(arguments.get(common.HED_XML_FILE, ''))

    results = string_validate(arguments, hed_schema)
    if results['data']:
        return results
    string_list = []
    conversion_errors = []
    for pos, string in enumerate(arguments.get(common.STRING_LIST), start=1):
        hed_string_obj = HedString(string)
        if arguments[common.COMMAND] == common.COMMAND_TO_LONG:
            issues = hed_string_obj.convert_to_long(hed_schema)
        else:
            issues = hed_string_obj.convert_to_short(hed_schema)
        if issues:
            conversion_errors.append(get_printable_issue_string(issues, f"Errors for HED string {pos}:"))
        string_list.append(str(hed_string_obj))

    if conversion_errors:
        category = 'warning'
        msg = 'Some strings had conversion errors'
    else:
        category = 'success'
        msg = 'Strings converted successfully'
    hed_version = hed_schema.header_attributes.get('version', 'Unknown version')
    if conversion_errors:
        return {'command': arguments.get('command', ''), 'data': conversion_errors, 'additional_info': string_list,
                'hed_version': hed_version, 'msg_category': 'warning',
                'msg': 'Some strings had conversion errors, results of conversion in additional_info'}
    else:
        return {'command': arguments.get('command', ''), 'data': string_list,
                'hed_version': hed_version, 'msg_category': 'success',
                'msg': 'Strings converted successfully'}


def string_validate(arguments, hed_schema=None):
    """Validates a hedstring and returns a dictionary containing the issues or a no errors message

    Parameters
    ----------
    arguments: dict
        Dictionary containing standard input form arguments
    hed_schema: str or HedSchema
        Version number or path or HedSchema object to be used

    Returns
    -------
    dict
        A dictionary with string_results as the key
    """

    if not hed_schema:
            hed_schema = get_hed_schema(arguments)
    if common.STRING_LIST in arguments:
        hed_strings = arguments[common.STRING_LIST]
    else:
        raise HedFileError('NoStringList', 'No list of HED strings was entered')
    hed_validator = HedValidator(hed_schema=hed_schema)
    issues = hed_validator.validate_input(hed_strings)
    validation_errors = []
    for i in range(len(hed_strings)):
        issue = issues[i]
        if issue:
            validation_errors.append(get_printable_issue_string(issue, f"Errors for HED string {i+1}:"))
    hed_version = hed_schema.header_attributes.get('version', 'Unknown version')
    if validation_errors:
        return {'command': arguments.get('command', ''), 'data': validation_errors,
                'hed_version': hed_version, 'msg_category': 'warning',
                'msg': 'Strings had validation errors'}
    else:
        return {'command': arguments.get('command', ''), 'data': '',
                'hed_version': hed_version, 'msg_category': 'success',
                'msg': 'Strings validated successfullly...'}
