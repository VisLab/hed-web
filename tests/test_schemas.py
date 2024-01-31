import os
import unittest
from werkzeug.test import create_environ
from werkzeug.wrappers import Request
from tests.test_web_base import TestWebBase
from hed.errors.exceptions import HedFileError
from hedweb.constants import base_constants
from hed import HedSchema, load_schema, load_schema_version
from hedweb.process_schemas import ProcessSchemas


class Test(TestWebBase):


    def test_set_input_from_schemas_form_valid(self):
        from hedweb.process_schemas import ProcessSchemas

        with self.app.test:
            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.0.0.xml')
            with open(schema_path, 'rb') as fp:
                environ = create_environ(data={base_constants.SCHEMA_FILE: fp,
                                               base_constants.SCHEMA_UPLOAD_OPTIONS: base_constants.SCHEMA_FILE_OPTION,
                                               base_constants.COMMAND_OPTION:  base_constants.COMMAND_CONVERT_SCHEMA})
            request = Request(environ)
            schema_proc = ProcessSchemas()
            schema_proc.set_input_from_form(request)
            # ----temporary
            schema_proc.command = base_constants.COMMAND_CONVERT_SCHEMA
            schema1 = schema_proc.schema
            self.assertTrue(schema1)
            self.assertIsInstance(schema1, HedSchema)

            self.assertEqual(schema_proc.command, base_constants.COMMAND_CONVERT_SCHEMA, "should have a command")
            self.assertFalse(schema_proc.check_for_warnings, "should have check_warnings false when not given")

    def test_schemas_process_empty(self):
        from hedweb.process_schemas import ProcessSchemas  
        with self.assertRaises(HedFileError):
            with self.app.app_context():
                proc_schemas = ProcessSchemas()
                proc_schemas.process()

    def test_schemas_check(self):
        with (self.app.app_context()):
            proc_schemas = ProcessSchemas()
            proc_schemas.command = base_constants.COMMAND_VALIDATE
            proc_schemas.schema = load_schema_version("8.0.0")
            results = proc_schemas.process()
            self.assertTrue(results['data'], "HED 8.0.0 is not fully HED-3G compliant")

            proc_schemas = ProcessSchemas()
            input_dict = {
                base_constants.COMMAND: base_constants.COMMAND_VALIDATE,
                base_constants.SCHEMA1: load_schema_version("8.0.0")
            }
            proc_schemas.set_input_from_dict(input_dict)
            results = proc_schemas.process()
            self.assertTrue(results['data'], "HED 8.0.0 is not fully HED-3G compliant")

        with self.app.app_context():
            proc_schemas = ProcessSchemas()
            proc_schemas.command = base_constants.COMMAND_VALIDATE
            proc_schemas.schema = load_schema_version("8.2.0")
            results = proc_schemas.process()
            self.assertFalse(results['data'], "HED8.0.0 is HED-3G compliant")

    def test_schemas_convert_valid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED8.2.0.mediawiki')
        name = "HED8.2.0"
        with self.app.app_context():
            proc_schemas = ProcessSchemas()
            proc_schemas.command = base_constants.COMMAND_CONVERT_SCHEMA
            proc_schemas.schema = load_schema(schema_path, name=name)
            results = proc_schemas.process()
            self.assertTrue(results['data'], "HED 8.2.0.mediawiki can be converted to xml")
            self.assertEqual(results['output_display_name'], "HED8.2.0.xml")

            proc_schemas = ProcessSchemas()
            input_dict = {
                base_constants.COMMAND: base_constants.COMMAND_CONVERT_SCHEMA,
                base_constants.SCHEMA1: load_schema(schema_path, name=name)
            }
            proc_schemas.set_input_from_dict(input_dict)
            results = proc_schemas.process()
            self.assertTrue(results['data'], "HED 8.2.0.mediawiki can be converted to xml")
            self.assertEqual(results['output_display_name'], "HED8.2.0.xml")

    def test_schemas_convert_invalid(self):
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HEDbad.xml')
        display_name = 'HEDbad'
        with self.assertRaises(HedFileError):
            with self.app.app_context():
                proc_schemas = ProcessSchemas()
                proc_schemas.command = base_constants.COMMAND_CONVERT_SCHEMA
                proc_schemas.schema = load_schema(schema_path, name=display_name)
                results = proc_schemas.process()
                self.assertTrue(results['data'], "Does not reach here, as it fails to load")

    def test_schemas_compare_valid(self):
        with self.app.app_context():
            proc_schemas = ProcessSchemas()
            proc_schemas.command = base_constants.COMMAND_COMPARE_SCHEMAS
            proc_schemas.schema = load_schema_version("8.1.0")
            proc_schemas.schema2 = load_schema_version("8.2.0")
            results = proc_schemas.process()
            self.assertTrue(results['data'], "HED 8.1.0/8.2.0 can be compared")
            # Check for some differences
            self.assertTrue("Attribute 'rooted' not in 'Schema1':" in results['data'])
            self.assertTrue("Tags: And, Comparative-relation, Connective-relation, Directional-relation, Ethnicity, Event-context, Gentalia, Inset, Logical-relation, Lower-center-of, Lower-left-of, Lower-right-of, Offset, Onset, Or, Performed-using, Race, Spatial-relation, Temporal-relation, Upper-center-of, Upper-left-of, Upper-right-of" in results['data'])
            self.assertTrue("elementProperty, isInheritedProperty, nodeProperty" in results['data'])

            input_dict = {
                base_constants.COMMAND: base_constants.COMMAND_COMPARE_SCHEMAS,
                base_constants.SCHEMA1: load_schema_version("8.1.0"),
                base_constants.SCHEMA2: load_schema_version("8.2.0")
            }
            proc_schemas = ProcessSchemas()
            proc_schemas.set_input_from_dict(input_dict)
            results = proc_schemas.process()
            self.assertTrue(results['data'], "HED 8.1.0/8.2.0 can be compared")

    def test_schemas_compare_identical(self):
        with self.app.app_context():
            proc_schemas = ProcessSchemas()
            proc_schemas.command = base_constants.COMMAND_COMPARE_SCHEMAS
            proc_schemas.schema = load_schema_version("8.2.0")
            proc_schemas.schema2 = load_schema_version("8.2.0")
            results = proc_schemas.process()
            self.assertFalse(results['data'], "HED 8.2.0/8.2.0 can be compared, but are identical")

    def test_schemas_compare_invalid(self):
        with self.app.app_context():
            with self.assertRaises(HedFileError):
                proc_schemas = ProcessSchemas()
                proc_schemas.command = base_constants.COMMAND_COMPARE_SCHEMAS
                proc_schemas.schema = load_schema_version("8.2.0")
                proc_schemas.process()

            with self.assertRaises(HedFileError):
                proc_schemas = ProcessSchemas()
                proc_schemas.command = base_constants.COMMAND_COMPARE_SCHEMAS
                proc_schemas.schema2 = load_schema_version("8.2.0")
                proc_schemas.process()

if __name__ == '__main__':
    unittest.main()
