from flask import render_template, Response, request, Blueprint, current_app
import os
import json
import traceback

from hed.util import hed_cache
from hed.schema import hed_schema_file
from hed.web import events, spreadsheet, schema, services, spreadsheet_utils
from hed.web.constants import common_constants, error_constants, page_constants, route_constants
from hed.web.web_utils import delete_file_if_it_exists, save_file_to_upload_folder, \
    generate_download_file_response, handle_http_error
from hed.web.dictionary import report_dictionary_validation_status

app_config = current_app.config
route_blueprint = Blueprint(route_constants.ROUTE_BLUEPRINT, __name__)


@route_blueprint.route(route_constants.DELETE_FILE_ROUTE, strict_slashes=False, methods=['GET'])
def delete_file_in_upload_directory(filename):
    """Deletes the specified other from the upload other.

    Parameters
    ----------
    filename: string
        The name of the other to delete from the upload other.

    Returns
    -------

    """
    if delete_file_if_it_exists(os.path.join(app_config['UPLOAD_FOLDER'], filename)):
        return Response(status=error_constants.NO_CONTENT_SUCCESS)
    else:
        return handle_http_error(error_constants.NOT_FOUND_ERROR, error_constants.FILE_DOES_NOT_EXIST)


@route_blueprint.route(route_constants.DOWNLOAD_FILE_ROUTE, strict_slashes=False, methods=['GET'])
def download_file_in_upload_directory(filename, header=None):
    """Downloads the specified file from the download folder.

    Parameters
    ----------
    filename: str
        The name of the file to download from the upload other.
    header: str
        Header string to be inserted in text files --- particularly files reporting errors or status

    Returns
    -------
    File
        The contents of a other in the upload directory to send to the client.

    """
    download_response = generate_download_file_response(filename, header)
    if not download_response or isinstance(download_response, str):
        handle_http_error(error_constants.NOT_FOUND_ERROR, download_response, as_text=True)
    return download_response


@route_blueprint.route(route_constants.DICTIONARY_VALIDATION_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_dictionary_validation_results():
    """Validate the JSON dictionary in the form after submission and return an attachment containing the output.

    Parameters
    ----------

    Returns
    -------
        download file
        A text file with the validation errors.
    """
    validation_response = report_dictionary_validation_status(request)
    return validation_response


@route_blueprint.route(route_constants.EVENTS_VALIDATION_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_events_validation_results():
    """Validate the spreadsheet in the form after submission and return an attachment other containing the output.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing information related to the worksheet columns. If the validation fails then a
        500 error message is returned.
    """
    validation_response = events.report_events_validation_status(request)
    # Success
    if isinstance(validation_response, Response):
        return validation_response
    if isinstance(validation_response, str):
        if validation_response:
            return handle_http_error(error_constants.INTERNAL_SERVER_ERROR, validation_response, as_text=True)
        else:
            return ""


@route_blueprint.route(route_constants.HED_SERVICES_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_hed_services_results():
    """Validate the hed strings associated with EEG events after submission from HEDTools EEGLAB plugin and
    return json string containing the output.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing information related to the EEG events' hed-strings.
        If the validation fails then a 500 error message is returned.
    """
    status = services.report_services_status(request)

    if error_constants.ERROR_KEY in status:
        return handle_http_error(error_constants.INTERNAL_SERVER_ERROR, status[error_constants.ERROR_KEY])
    return json.dumps(status)


@route_blueprint.route(route_constants.HED_VERSION_ROUTE, methods=['POST'])
def get_hed_version():
    """Finds the information about the HED version of a file and returns as JSON.

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing information related to the spreadsheet columns.

    """
    hed_info = {}
    try:
        if common_constants.HED_XML_FILE in request.files:
            hed_file_path = save_file_to_upload_folder(request.files[common_constants.HED_XML_FILE])
            hed_info[common_constants.HED_VERSION] = hed_schema_file.get_hed_xml_version(hed_file_path)
    except:
        return handle_http_error(error_constants.INTERNAL_SERVER_ERROR, traceback.format_exc())
    return json.dumps(hed_info)


@route_blueprint.route(route_constants.HED_MAJOR_VERSION_ROUTE, methods=['GET'])
def get_major_hed_versions():
    """Gets information related to the spreadsheet columns.

    This information contains the names of the spreadsheet columns and column indices that contain HED tags.

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing information related to the spreadsheet columns.

    """
    hed_info = {}
    try:
        hed_cache.cache_all_hed_xml_versions()
        hed_info[common_constants.HED_MAJOR_VERSIONS] = hed_cache.get_all_hed_versions()
    except:
        return handle_http_error(error_constants.INTERNAL_SERVER_ERROR, traceback.format_exc())
    return json.dumps(hed_info)


@route_blueprint.route(route_constants.SCHEMA_COMPLIANCE_CHECK_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_schema_compliance_check_results():
    """Check the HED specification in the form after submission and return an attachment other containing the output.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing the hed specification to check. If the conversion fails then a
        500 error message is returned.
    """
    comparison_response = schema.run_schema_compliance_check(request)
    # Success
    if isinstance(comparison_response, Response):
        return comparison_response
    if isinstance(comparison_response, str):
        if comparison_response:
            return handle_http_error(error_constants.INTERNAL_SERVER_ERROR, comparison_response, as_text=True)
        else:
            return ""

    return handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                             "Invalid duplicate tag check. This should not happen.", as_text=True)


@route_blueprint.route(route_constants.SCHEMA_CONVERSION_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_schema_conversion_results():
    """Convert the given HED specification and return an attachment with the result.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing information related file to convert. If the conversion fails then a
        500 error message is returned.
    """
    conversion_response = schema.run_schema_conversion(request)
    # Success
    if isinstance(conversion_response, Response):
        return conversion_response
    if isinstance(conversion_response, str):
        return handle_http_error(error_constants.INTERNAL_SERVER_ERROR, conversion_response, as_text=True)

    return handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                             "Invalid response type in get_duplicate_tag_results.  This should not happen.",
                             as_text=True)


@route_blueprint.route(route_constants.SPREADSHEET_COLUMN_INFO_ROUTE, methods=['POST'])
def get_spreadsheet_columns_info():
    """Gets information related to the spreadsheet columns.

    This information contains the names of the spreadsheet columns and column indices that contain HED tags.

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing information related to the spreadsheet columns.

    """
    spreadsheet_columns_info = spreadsheet_utils.find_spreadsheet_columns_info(request)
    if error_constants.ERROR_KEY in spreadsheet_columns_info:
        return handle_http_error(error_constants.INTERNAL_SERVER_ERROR,
                                 spreadsheet_columns_info[error_constants.ERROR_KEY])
    return json.dumps(spreadsheet_columns_info)


@route_blueprint.route(route_constants.SPREADSHEET_VALIDATION_SUBMIT_ROUTE, strict_slashes=False, methods=['POST'])
def get_spreadsheet_validation_results():
    """Validate the spreadsheet in the form after submission and return an attachment other containing the output.

    Parameters
    ----------

    Returns
    -------
        string
        A serialized JSON string containing information related to the worksheet columns. If the validation fails then a
        500 error message is returned.
    """
    validation_response = spreadsheet.report_spreadsheet_validation_status(request)
    # Success
    if isinstance(validation_response, Response):
        return validation_response
    if isinstance(validation_response, str):
        if validation_response:
            return handle_http_error(error_constants.INTERNAL_SERVER_ERROR, validation_response, as_text=True)
        else:
            return ""


@route_blueprint.route(route_constants.WORKSHEET_COLUMN_INFO_ROUTE, methods=['POST'])
def get_worksheets_info():
    """Gets information related to the Excel worksheets.

    This information contains the names of the worksheets in a workbook, the names of the columns in the first
    worksheet, and column indices that contain HED tags in the first worksheet.

    Parameters
    ----------

    Returns
    -------
    string
        A serialized JSON string containing information related to the Excel worksheets.

    """
    worksheets_info = {common_constants.WORKSHEET_NAMES: [], common_constants.COLUMN_NAMES: [],
                       common_constants.TAG_COLUMN_INDICES: []}
    workbook_file_path = ''
    try:
        if common_constants.SPREADSHEET_FILE in request.files:
            workbook_file = request.files[common_constants.SPREADSHEET_FILE]
            workbook_file_path = save_file_to_upload_folder(workbook_file)
            if workbook_file_path:
                worksheets_info = spreadsheet_utils.populate_worksheets_info_dictionary(worksheets_info, workbook_file_path)
    except:
        worksheets_info[error_constants.ERROR_KEY] = traceback.format_exc()
    finally:
        delete_file_if_it_exists(workbook_file_path)
    return json.dumps(worksheets_info)


@route_blueprint.route(route_constants.ADDITIONAL_EXAMPLES_ROUTE, strict_slashes=False, methods=['GET'])
def render_additional_examples_page():
    """Handles the site additional examples page.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the additional examples page.

    """
    return render_template(page_constants.ADDITIONAL_EXAMPLES_PAGE)


@route_blueprint.route(route_constants.COMMON_ERRORS_ROUTE, strict_slashes=False, methods=['GET'])
def render_common_error_page():
    """Handles the common errors page.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the home page.

    """
    return render_template(page_constants.COMMON_ERRORS_PAGE)


@route_blueprint.route(route_constants.DICTIONARY_ROUTE, strict_slashes=False, methods=['GET'])
def render_dictionary_form():
    """Handles the site root and Validation tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the validation form. If the HTTP method is a GET then the validation form will be
        displayed. If the HTTP method is a POST then the validation form is submitted.

    """
    return render_template(page_constants.DICTIONARY_VALIDATION_PAGE)
    # return render_template(page_constants.DICTIONARY_VALIDATION_PAGE)


@route_blueprint.route(route_constants.EVENTS_ROUTE, strict_slashes=False, methods=['GET'])
def render_events_form():
    """Handles the site root and Validation tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the validation form. If the HTTP method is a GET then the validation form will be
        displayed. If the HTTP method is a POST then the validation form is submitted.

    """
    return render_template(page_constants.EVENTS_PAGE)


@route_blueprint.route(route_constants.HED_SERVICES_ROUTE, strict_slashes=False, methods=['GET'])
def render_hed_services_form():
    """Handles the site root and EEG Validation tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the validation form. If the HTTP method is a GET then the validation form will be
        displayed. If the HTTP method is a POST then the validation form is submitted.

    """
    return render_template(page_constants.HED_SERVICES_PAGE)


@route_blueprint.route(route_constants.HED_TOOLS_HELP_ROUTE, strict_slashes=False, methods=['GET'])
def render_help_page():
    """Handles the site help page.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the help page.

    """
    return render_template(page_constants.HED_TOOLS_HELP_PAGE)


@route_blueprint.route(route_constants.HED_TOOLS_HOME_ROUTE, strict_slashes=False, methods=['GET'])
def render_home_page():
    """Handles the home page.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the home page.

    """
    return render_template(page_constants.HED_TOOLS_HOME_PAGE)


@route_blueprint.route(route_constants.SCHEMA_ROUTE, strict_slashes=False, methods=['GET'])
def render_schema_form():
    """Handles the site root and conversion tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the conversion form. If the HTTP method is a GET then the conversion form will be
        displayed. If the HTTP method is a POST then the conversion form is submitted.

    """
    return render_template(page_constants.SCHEMA_PAGE)


@route_blueprint.route(route_constants.SPREADSHEET_ROUTE, strict_slashes=False, methods=['GET'])
def render_spreadsheet_form():
    """Handles the site root and Validation tab functionality.

    Parameters
    ----------

    Returns
    -------
    Rendered template
        A rendered template for the validation form. If the HTTP method is a GET then the validation form will be
        displayed. If the HTTP method is a POST then the validation form is submitted.

    """
    return render_template(page_constants.SPREADSHEET_PAGE)