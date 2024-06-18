from hed.errors import get_printable_issue_string, HedFileError
from hed.schema.schema_compare import compare_differences
from hed import schema as hedschema
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from hedweb.web_util import generate_filename, get_parsed_name
from hedweb.constants import base_constants as bc
from hedweb.constants import file_constants as fc
from hedweb.base_operations import BaseOperations


class SchemaOperations(BaseOperations):

    def __init__(self, arguments=None):
        """ Construct a SchemaOperations object to handle sidecar operations.

        Parameters:
             arguments (dict): Dictionary with parameters extracted from form or service

        """
        super().__init__()
        self.schema = None
        self.schema2 = None
        self.command = None
        self.check_for_warnings = False
        if arguments:
            self.set_input_from_dict(arguments)

    def process(self):
        """ Perform the requested action for the schema.
    
        Returns:
            dict: A dictionary of results in the standard results format.
    
        Raises:
            HedFileError:  If the command was not found or the input arguments were not valid.
    
        """
        if not self.command:
            raise HedFileError('MissingCommand', 'Command is missing', '')
        if not self.schema:
            raise HedFileError("SCHEMA_NOT_FOUND", "Must provide a source schema", "")
        if self.command == bc.COMMAND_VALIDATE:
            results = self.validate()
        elif self.command == bc.COMMAND_COMPARE_SCHEMAS:
            if not self.schema2:
                raise HedFileError("SCHEMA_NOT_FOUND", "Must provide a compare schema", "")
            results = self.compare()
        elif self.command == bc.COMMAND_CONVERT_SCHEMA:
            results = self.convert()
        else:
            raise HedFileError('UnknownProcessingMethod', "Select a schema processing method", "")
        return results

    def compare(self):
        data = compare_differences(self.schema, self.schema2)
        output_name = self.schema.name + '_' + self.schema2.name + '_' + "differences.txt"
        msg_results = ''
        if not data:
            msg_results = ': no differences found'
        return {'command': bc.COMMAND_COMPARE_SCHEMAS,
                bc.COMMAND_TARGET: 'schema',
                'data': data,
                'output_display_name': output_name,
                'schema_version': self.schema.get_formatted_version(),
                'schema2_version': self.schema2.get_formatted_version(),
                'msg_category': 'success',
                'msg': 'Schemas were successfully compared' + msg_results}

    def convert(self):
        """ Return a string representation of hed_schema in format determined by the display name extension.
      
        Returns:
            dict: A dictionary of results in the standard results format.
    
        """

        if self.schema.source_format == fc.SCHEMA_XML_EXTENSION:
            data = self.schema.get_as_mediawiki_string()
            extension = '.mediawiki'
        else:
            data = self.schema.get_as_xml_string()
            extension = '.xml'
        file_name = self.schema.name + extension

        return {'command': bc.COMMAND_CONVERT_SCHEMA,
                bc.COMMAND_TARGET: 'schema',
                'data': data,
                'output_display_name': file_name,
                'schema_version': self.schema.get_formatted_version(),
                'msg_category': 'success',
                'msg': 'Schema was successfully converted'}

    def validate(self):
        """ Run schema compliance for HED-3G.
        
        Returns:
            dict: A dictionary of results in the standard results format.
    
        """

        issues = self.schema.check_compliance(self.check_for_warnings)
        if issues:
            issue_str = get_printable_issue_string(issues, f"Schema issues for {self.schema.name}:")
            file_name = self.schema.name + 'schema_issues.txt'
            return {'command': bc.COMMAND_VALIDATE,
                    bc.COMMAND_TARGET: 'schema',
                    'data': issue_str,
                    'output_display_name': file_name,
                    'schema_version': self.schema.get_formatted_version(),
                    'msg_category': 'warning',
                    'msg': 'Schema has validation issues'}
        else:
            return {'command': bc.COMMAND_VALIDATE,
                    bc.COMMAND_TARGET: 'schema',
                    'data': '',
                    'output_display_name': self.schema.name,
                    'schema_version': self.schema.get_formatted_version(),
                    'msg_category': 'success',
                    'msg': 'Schema had no validation issues'}

    @staticmethod
    def format_error(command, exception):
        issue_str = get_printable_issue_string(exception.issues, f"Schema issues for {exception.filename}:")
        file_name = generate_filename(exception.filename, name_suffix='_issues', extension='.txt')
        return {'command': command,
                bc.COMMAND_TARGET: 'schema',
                'data': issue_str,
                'output_display_name': file_name,
                'msg_category': 'warning',
                'msg': 'Schema had issues'
                }


def get_schema(schema_input=None, version=None, as_xml_string=None):
    """ Return a HedSchema object from the given parameters.

    Parameters:
        schema_input (str or FileStorage or None): Input url or file
        version (str or None): A schema version string to load, e.g. "8.2.0" or "score_1.1.0"
        as_xml_string (str or None): A schema in xml string format
    Returns:
        HedSchema: Schema

    :raises HedFileError:
        - The schema can't be loaded for some reason
    """
    if isinstance(schema_input, FileStorage):
        name, extension = get_parsed_name(secure_filename(schema_input.filename))
        hed_schema = hedschema.from_string(schema_input.read(fc.BYTE_LIMIT).decode('utf-8'),
                                           schema_format=extension,
                                           name=name)
    elif isinstance(schema_input, str):
        name, extension = get_parsed_name(schema_input, is_url=True)
        hed_schema = hedschema.load_schema(schema_input, name=name)
    elif isinstance(version, str):
        return hedschema.load_schema_version(version)
    elif isinstance(as_xml_string, str):
        return hedschema.from_string(as_xml_string, schema_format=".xml")
    else:
        raise HedFileError("SCHEMA_NOT_FOUND", "Must provide a loadable schema", "")

    return hed_schema
