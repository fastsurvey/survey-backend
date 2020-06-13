from cerberus import Validator, TypeDefinition


class SubmissionValidator(Validator):
    """The cerberus submission validator with added custom validation rules.

    For an explanation of the validation rules we kindly refer the curious
    reader to the FastSurvey and the cerberus documentations. They are omitted 
    here to avoid documentation duplication and to keep the methods as 
    overseeable as possible.
    
    """

    types_mapping = {
        'Email': TypeDefinition('Email', (str,), ()),
        'Properties': TypeDefinition('Properties', (dict,), ()),
        'Selection': TypeDefinition('Selection', (dict,), ()),
        'List': TypeDefinition('List', (str,), ()),
        'Option': TypeDefinition('Option', (bool,), ()),
        'Text': TypeDefinition('Text', (str,), ()),
    }

    @classmethod
    def create(cls, configuration):
        """Factory method providing a simple interface to create a validator.

        A more elegant way to achieve this would be to override the __init__
        method of the Validator class. The __init__ method is somehow called 
        multiple times, though, that's why using a factory method is the 
        easier way.

        """
        return cls(
            _generate_schema(configuration), 
            require_all=True,
        )
    
    def _validate_min_chars(self, min_chars, field, value):
        """{'type': 'integer'}"""
        if len(value) < min_chars:
            self._error(field, f'Must be at least {min_chars} characters long') 
  
    def _validate_max_chars(self, max_chars, field, value):
        """{'type': 'integer'}"""
        if len(value) > max_chars:
            self._error(field, f'Must be at most {max_chars} characters long') 

    def _count_selections(self, value):
        """Count the number of selected options in a selection field."""
        count = 0
        for v in value.values():
            if isinstance(v, bool) and v:  # for option children
                count += 1
            if isinstance(v, str):  # for list children
                split = set([e.strip() for e in v.split(',') if e.strip()])
                count += len(split)
        return count

    def _validate_min_select(self, min_select, field, value):
        """{'type': 'integer'}"""
        if self._count_selections(value) < min_select:
            self._error(field, f'Must select at least {min_select} options')

    def _validate_max_select(self, max_select, field, value):
        """{'type': 'integer'}"""
        if self._count_selections(value) > max_select:
            self._error(field, f'Must select at most {max_select} options')


def _generate_schema(configuration):
    """Generate the cerberus validation schema from a survey configuration."""

    def _generate_field_schema(field):
        """Recursively generate the cerberus schemas for a survey field."""
        fs = {'type': field['type']}
        if 'properties' in field.keys():
            if 'fields' in field['properties'].keys():
                fs['schema'] = {
                    str(i+1): _generate_field_schema(child)
                    for i, child
                    in enumerate(field['properties']['fields'])
                }
            for k, v in field['properties'].items():
                if k != 'fields':
                    fs[k] = v
        return fs

    schema = {
        'email': {
            'type': 'Email',
            'regex': r'^[a-z]{2}[0-9]{2}[a-z]{3}@mytum\.de$',
        },
        'properties': {
            'type': 'Properties',
            'schema': {
                str(i+1): _generate_field_schema(field)
                for i, field
                in enumerate(configuration['fields'])
            },
        },
    }
    return schema