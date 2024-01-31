import os
import io
import json
from flask import current_app
from hed.models.hed_string import HedString
from hed.models.sidecar import Sidecar
from hed.models.spreadsheet_input import SpreadsheetInput
from hed.models.tabular_input import TabularInput
from hed.errors import HedFileError
from hed import schema as hedschema
from hedweb.constants import base_constants
from hedweb.columns import get_column_names
from hedweb.process_events import ProcessEvents
from hedweb.process_schemas import ProcessSchemas
from hedweb.process_spreadsheets import ProcessSpreadsheets
from hedweb.process_sidecars import ProcessSidecars
from hedweb.process_strings import ProcessStrings


class ProcessServices:

    def __init__(self):
        self.temp = None

    @staticmethod
    def set_input_from_request(request):
        """ Get a dictionary of input from a service request.

        Args:
            request (Request): A Request object containing user data for the service request.

        Returns:
            dict: A dictionary containing input arguments for calling the service request.

        """

        form_data = request.data
        form_string = form_data.decode()
        service_request = json.loads(form_string)
        arguments = ProcessServices.get_service_info(service_request)
        arguments[base_constants.SCHEMA] = ProcessServices.set_input_schema(service_request)
        ProcessServices.set_column_parameters(arguments, service_request)
        ProcessServices.set_remodel_parameters(arguments, service_request)
        ProcessServices.set_sidecar(arguments, service_request)
        ProcessServices.set_input_objects(arguments, service_request)
        arguments[base_constants.QUERY] = service_request.get('query', None)
        return arguments

    @staticmethod
    def set_column_parameters(arguments, params):
        """ Update arguments with the columns that requested for the service.

        Args:
            arguments (dict):  A dictionary with the extracted parameters that are to be processed.
            params (dict): The service request dictionary extracted from the Request object.

        Updates the arguments dictionary with the column information in service_request.

        """

        columns_selected = {}
        if base_constants.COLUMNS_CATEGORICAL in params:
            for column in params[base_constants.COLUMNS_CATEGORICAL]:
                columns_selected[column] = True
        if base_constants.COLUMNS_VALUE in params:
            for column in params[base_constants.COLUMNS_VALUE]:
                columns_selected[column] = False
        arguments[base_constants.COLUMNS_SELECTED] = columns_selected
        columns_included = []
        if base_constants.COLUMNS_INCLUDED in params:
            for column in params[base_constants.COLUMNS_INCLUDED]:
                columns_included.append(column)
        arguments[base_constants.COLUMNS_INCLUDED] = columns_included
        arguments[base_constants.TAG_COLUMNS] = get_column_names(params)
        arguments[base_constants.HAS_COLUMN_NAMES] = True

    @staticmethod
    def set_sidecar(arguments, params):
        """ Update arguments with the sidecars if there are any.

         Args:
             arguments (dict):  A dictionary with the extracted parameters that are to be processed.
             params (dict): The service request dictionary extracted from the Request object.

         Updates the arguments dictionary with the sidecars.

         """
        sidecar_list = []
        if base_constants.SIDECAR_STRING in params and params[base_constants.SIDECAR_STRING]:
            sidecar_list = params[base_constants.SIDECAR_STRING]
            if not isinstance(sidecar_list, list):
                sidecar_list = [sidecar_list]
        if sidecar_list:
            file_list = []
            for s_string in sidecar_list:
                file_list.append(io.StringIO(s_string))
            arguments[base_constants.SIDECAR] = Sidecar(files=file_list, name="Merged_Sidecar")
        else:
            arguments[base_constants.SIDECAR] = None

    @staticmethod
    def set_input_objects(arguments, params):
        """ Update arguments with the information in the params dictionary.

        Args:
            arguments (dict):  A dictionary with the extracted parameters that are to be processed.
            params (dict): A dictionary of the service request values.

        Updates the arguments dictionary with the input objects including events, spreadsheets, schemas or strings.

        """

        schema = arguments.get('schema', None)
        if base_constants.EVENTS_STRING in params and params[base_constants.EVENTS_STRING]:
            arguments[base_constants.EVENTS] = \
                TabularInput(file=io.StringIO(params[base_constants.EVENTS_STRING]),
                             sidecar=arguments.get(base_constants.SIDECAR, None), name='Events')
        if base_constants.SPREADSHEET_STRING in params and params[base_constants.SPREADSHEET_STRING]:
            arguments[base_constants.SPREADSHEET] = \
                SpreadsheetInput(file=io.StringIO(params[base_constants.SPREADSHEET_STRING]), file_type=".tsv",
                                 tag_columns=arguments[base_constants.TAG_COLUMNS], 
                                 has_column_names=True, column_prefix_dictionary=None, name='spreadsheets.tsv')
        if base_constants.STRING_LIST in params and params[base_constants.STRING_LIST]:
            s_list = []
            for s in params[base_constants.STRING_LIST]:
                s_list.append(HedString(s, hed_schema=schema))
            arguments[base_constants.STRING_LIST] = s_list

    @staticmethod
    def set_remodel_parameters(arguments, params):
        """ Update arguments with the remodeler information if any.

         Args:
             arguments (dict):  A dictionary with the extracted parameters that are to be processed.
             params (dict): The service request dictionary extracted from the Request object.

         Updates the arguments dictionary with the sidecars.

         """

        if base_constants.REMODEL_STRING in params:
            arguments[base_constants.REMODEL_OPERATIONS] = \
                {'name': 'remodel_commands.json', 'operations': json.loads(params[base_constants.REMODEL_STRING])}

    @staticmethod
    def get_service_info(params):
        """ Get a dictionary with the service request command information filled in.

        Args:
            params (dict): A dictionary of the service request values.

        Returns:
            dict: A dictionary with the command, command target and options resolved from the service request.

        """
        service = params.get(base_constants.SERVICE, '')
        command = service
        command_target = ''
        pieces = service.split('_', 1)
        if command != "get_services" and len(pieces) == 2:
            command = pieces[1]
            command_target = pieces[0]
        has_column_names = True
        expand_defs = params.get(base_constants.EXPAND_DEFS, '') == 'on'
        check_for_warnings = params.get(base_constants.CHECK_FOR_WARNINGS, '') == 'on'
        include_description_tags = params.get(base_constants.INCLUDE_DESCRIPTION_TAGS, '') == 'on'

        return {base_constants.SERVICE: service,
                base_constants.COMMAND: command,
                base_constants.COMMAND_TARGET: command_target,
                base_constants.HAS_COLUMN_NAMES: has_column_names,
                base_constants.CHECK_FOR_WARNINGS: check_for_warnings,
                base_constants.EXPAND_DEFS: expand_defs,
                base_constants.INCLUDE_DESCRIPTION_TAGS: include_description_tags
                }

    @staticmethod
    def set_input_schema(parameters):
        """ Get a HedSchema or HedSchemaGroup object from the parameters.

        Args:
            parameters (dict): A dictionary of parameters extracted from the service request.

        """
        # the_schema = None
        # try:
        if base_constants.SCHEMA_STRING in parameters and parameters[base_constants.SCHEMA_STRING]:
            the_schema = hedschema.from_string(parameters[base_constants.SCHEMA_STRING])
        elif base_constants.SCHEMA_URL in parameters and parameters[base_constants.SCHEMA_URL]:
            schema_url = parameters[base_constants.SCHEMA_URL]
            the_schema = hedschema.load_schema(schema_url)
        elif base_constants.SCHEMA_VERSION in parameters and parameters[base_constants.SCHEMA_VERSION]:
            versions = parameters[base_constants.SCHEMA_VERSION]
            the_schema = hedschema.load_schema_version(versions)
        # except HedFileError:
        #     the_schema = None

        return the_schema

    @staticmethod
    def process(arguments):
        """ Call the desired service processing function and return the results in a standard format.

        Args:
            arguments (dict): A dictionary of arguments for the processing resolved from the request.

        Returns:
            dict: A dictionary of results in standard response format to be jsonified.

        """

        response = {base_constants.SERVICE: arguments.get(base_constants.SERVICE, ''),
                    'results': {}, 'error_type': '', 'error_msg': ''}
        if arguments.get(base_constants.COMMAND, '') == 'get_services':
            response["results"] = ProcessServices.get_services_list()
        else:
            proc_obj = ProcessServices.get_process(arguments.get(base_constants.COMMAND_TARGET, ''))
            if not proc_obj:
                response["error_type"] = 'HEDServiceInvalid'
                response["error_msg"] = "Must specify a valid service"
                return
     
            proc_obj.set_input_from_dict(arguments)
            response["results"] = proc_obj.process()
        results = response.get("results", {})
        results["software_version"] = current_app.config['VERSIONS']
        results = ProcessServices.package_spreadsheet(results)
        response["results"] = results
        return response
    
    @staticmethod
    def get_process(target):
        """ Return the BaseProcess object specific to the target string. 
        
        Parameters:
            target (str): Indicates what type of BaseProcess is needed. 
            
        Returns:
            BaseProcess:  A processing object of class BaseProcess
        
        """
        if target == "events":
            proc_obj = ProcessEvents()
        elif target == "sidecar":
            proc_obj = ProcessSidecars()
        elif target == "spreadsheet":
            proc_obj = ProcessSpreadsheets()
        elif target == "strings":
            proc_obj = ProcessStrings()
        elif target == "schemas":
            proc_obj = ProcessSchemas()
        else:
            raise HedFileError('InvalidTargetForProcessing', f'Target "{target}" is missing or invalid', '')
        return proc_obj

    @staticmethod
    def package_spreadsheet(results):
        """ Get the transformed results dictionary where spreadsheets are converted to strings.

        Args:
            results (dict): The dictionary of results in standardized form returned from processing.

        Returns:
            dict: The results transformed so that all entries are strings.


        """
        if results['msg_category'] == 'success' and results.get(base_constants.SPREADSHEET, ''):
            results[base_constants.SPREADSHEET] = results[base_constants.SPREADSHEET].to_csv(file=None)
        elif base_constants.SPREADSHEET in results:
            del results[base_constants.SPREADSHEET]
        return results

    @staticmethod
    def get_services_list():
        """ Get a formatted string describing services using the resources/services.json file

         Returns:
            dict: dictionary in standard form with data as formatted string of services.

         """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        the_path = os.path.join(dir_path, 'static/resources/services.json')
        with open(the_path) as f:
            service_info = json.load(f)
        services = service_info['services']
        meanings = service_info['parameter_meanings']
        returns = service_info['returns']
        results = service_info['results']

        ver = current_app.config['VERSIONS']
        services_string = f"\nServices:\n\tHEDTools version: {ver['tool_ver']} Date: {ver['tool_date']}\n" \
                          f"\tHEDServices version: {ver['web_ver']} Date: {ver['web_date']}"
        for service, info in services.items():
            description = info['Description']
            parameters = ProcessServices.get_parameter_string(info['Parameters'])

            return_string = info['Returns']
            next_string = \
                f'\n{service}:\n\tDescription: {description}\n{parameters}\n\tReturns: {return_string}\n'
            services_string += next_string

        meanings_string = '\nParameter meanings:\n'
        for string, meaning in meanings.items():
            meanings_string += f'\t{string}: {meaning}\n'

        returns_string = '\nReturn values:\n'
        for return_val, meaning in returns.items():
            returns_string += f'\t{return_val}: {meaning}\n'

        results_string = '\nResults field meanings:\n'
        for result_val, meaning in results.items():
            results_string += f'\t{result_val}: {meaning}\n'
        data = services_string + meanings_string + returns_string + results_string
        return {base_constants.COMMAND: 'get_services', base_constants.COMMAND_TARGET: '',
                'data': data, 'output_display_name': '',
                base_constants.SCHEMA_VERSION: '', 'msg_category': 'success',
                'msg': "List of available services and their meanings"}

    @staticmethod
    def get_parameter_string(params):
        if not params:
            return "\tParameters: []"
        param_list = []
        for p in params:
            if isinstance(p, list):
                param_list.append(" or ".join(p))
            else:
                param_list.append(p)

        return "\tParameters:\n\t\t" + "\n\t\t".join(param_list)