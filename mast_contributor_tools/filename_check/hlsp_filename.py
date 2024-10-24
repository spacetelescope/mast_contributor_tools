# shaw@stsci.edu
from abc import ABC, abstractmethod
import os
from pathlib import Path
import re
import yaml

# Fetch configurations for the module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'config.yaml'),'r') as f:
    cfg = yaml.safe_load(f)

EXTENSION_TYPES = cfg['ExtensionTypes']
SEMANTIC_TYPES = cfg['SemanticTypes']
fieldLengthPolicy = cfg['FieldLength']

# Fetch lists of missions, instruments, filters
#MISSIONS = ['hst','iue', 'jwst','tess']
#INSTRUMENTS = ['miri','nircam','niriss','nirspec','acs','cos','stis','wfc3']
#FILTERS = ['f100lp','f170lp','f290lp','g140h','g235h','g395h','f555w']

with open(os.path.join(BASE_DIR, 'oif.yaml'),'r') as f:
    oif = yaml.safe_load(f)

MISSIONS = [*oif]
INSTRUMENTS = set(sum([[*oif[m]['instruments']] for m in MISSIONS], []))
filt_list = []
for m in MISSIONS:
    for i in [*oif[m]['instruments']]:
        for f in [*oif[m]['instruments'][i]['filters']]:
            filt_list.append(f)
    
FILTERS = set(filt_list)

SCORE = {False: 'fail',
         True: 'pass'}

class FieldRule():
    """Rules for filename validation.
    
    This class embodies rules for validating attributes of field names. The 
    approach to validiting field *values* varies by field. The expressions that 
    validate the version or target fields can be verified at https://regex101.com
    """
    version_expr = re.compile("^v[1-9][\d]?((\.\d{1,2})(\.[a-z0-9]{1,2})?)?$")
    target_expr = re.compile("^[a-zA-Z][a-zA-Z\d+-.]*[a-zA-Z0-9]$")
    
    def length(value: str, max_length: int) -> bool:
        return len(value) <= max_length
    
    def capitalization(value: str) -> bool:
        return value.islower()
    
    # Rules for field values
    def matchTarget(value: str) -> bool:
        return FieldRule.target_expr.match(value) is not None
    
    def matchVersion(value: str) -> bool:
        return FieldRule.version_expr.match(value) is not None
    
    def matchChoice(value: str, choice_list: list[str]) -> bool:
        return value.lower() in choice_list
    
    def matchMultiChoice(value: str, choice_list: list[str]) -> bool:
        # match all elements in a hyphenated value to the choice_list
        return all([(v.lower() in choice_list) for v in value.split('-')])
    
    def severity(condition: bool) -> str: 
        if condition: 
            return 'N/A'
        else:
            return 'fatal'
    
    def severity_lax(condition: bool) -> str: 
        if condition: 
            return 'N/A'
        else:
            return 'unrecognized'


class FilenameFieldAB(ABC):
    """Template for Filename Field classes.
    
    Each field of a filename in an HLSP collection will be evaluated for: 
    length, capitalization, and often a match against valid values. 
    Each evaluation results in a score, which is one of: 
    - 'pass'
    - 'fail' 
    - 'N/A' 
    - 'unrecognized'

    The overall severity of the set of evaluations is one of: 
    - 'N/A' for no detected problem
    - 'fatal' for a detected problem that must be fixed
    - 'unrecognized' for a possible but non-fatal problem

    Parameters
    ----------
    field_name : str
        Internal name for the field being created
    field_value : str
        Value of the field (i.e. text of the field in the filename)
    """
    def __init__(self, 
                 field_name: str,
                 field_value: str) -> None:
        self.name = field_name
        self.value = field_value
        self.max_len = fieldLengthPolicy[field_name]
        self.cap_eval = False
        self.len_eval = False
        self.value_eval = False
        self.severity = 'fatal'
        #print(f'Creating {self.name} field with value {self.value}')
    
    @abstractmethod
    def evaluate(self):
        self.cap_eval = FieldRule.capitalization(self.value)
        self.len_eval = FieldRule.length(self.value, self.max_len)
    
    def get_scores(self):
        return {
            'name': self.name,
            'capitalization': SCORE[self.cap_eval],
            'length': SCORE[self.len_eval],
            'value': SCORE[self.value_eval],
            'severity': self.severity,
        }


class ExtensionField(FilenameFieldAB):
    """A container for attributes of the filename Extension field.
    """
    def __init__(self, 
                 value: str) -> None:
        super().__init__('extension', value)
    
    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.matchChoice(self.value, EXTENSION_TYPES)
        self.severity = FieldRule.severity(self.cap_eval and self.len_eval and self.value_eval)


class FilterField(FilenameFieldAB):
    """A container for attributes of the filename Filtername field.
    """
    def __init__(self, 
                 value: str) -> None:
        super().__init__('filter', value)
    
    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.matchMultiChoice(self.value, FILTERS)
        self.severity = FieldRule.severity(self.cap_eval and self.len_eval and self.value_eval)


class HlspField(FilenameFieldAB):
    """A container for attributes of the literal 'hlsp' prefix field.
    """
    def __init__(self, 
                 value: str) -> None:
        super().__init__('hlsp_str', value)
    
    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.matchChoice(self.value, ['hlsp'])
        self.severity = FieldRule.severity(self.cap_eval and self.len_eval and self.value_eval)


class HlspNameField(FilenameFieldAB):
    """A container for attributes of the HLSP name field.
    """
    def __init__(self, 
                 value: str,
                 ref_name: str) -> None:
        super().__init__('hlsp_name', value)
        self.hlsp_ref_name = ref_name
    
    def evaluate(self):
        super().evaluate()
        # Assume a valid HLSP name was passed to the constructor
        #self.value_eval = True
        self.value_eval = FieldRule.matchChoice(self.value, [self.hlsp_ref_name])
        self.severity = FieldRule.severity(self.cap_eval and self.len_eval and self.value_eval)


class InstrumentField(FilenameFieldAB):
    """A container for attributes of the filename Instrument field.
    """
    def __init__(self, 
                 value: str) -> None:
        super().__init__('instrument', value)
    
    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.matchMultiChoice(self.value, INSTRUMENTS)
        self.severity = FieldRule.severity(self.cap_eval and self.len_eval and self.value_eval)


class MissionField(FilenameFieldAB):
    """A container for attributes of the filename Mission (or observatory) field.
    """
    def __init__(self, 
                 value: str) -> None:
        super().__init__('mission', value)
        
    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.matchMultiChoice(self.value, MISSIONS)
        self.severity = FieldRule.severity(self.cap_eval and self.len_eval and self.value_eval)


class ProductField(FilenameFieldAB):
    """A container for attributes of the filename ProductType field.
    """
    def __init__(self, 
                 value: str) -> None:
        super().__init__('product_type', value)
    
    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.matchChoice(self.value, SEMANTIC_TYPES)
        self.severity = FieldRule.severity(self.cap_eval and self.len_eval)
        self.severity = FieldRule.severity_lax(self.severity and self.value_eval)


class TargetField(FilenameFieldAB):
    """A container for attributes of the filename TargetName field.
    """
    def __init__(self, 
                 value: str) -> None:
        super().__init__('target_name', value)
    
    def evaluate(self):
        super().evaluate()
        # A valid target name may contain the following characters in addition to 
        # alpha-numeric: + - .
        # but must begin and end with a purely alphanumeric character.
        self.value_eval = FieldRule.matchTarget(self.value)
        self.severity = FieldRule.severity(self.cap_eval and self.len_eval)
        self.severity = FieldRule.severity_lax(self.severity and self.value_eval)


class VersionField(FilenameFieldAB):
    """A container for attributes of the filename Version field.
    """
    def __init__(self, 
                 value: str) -> None:
        super().__init__('version_id', value)
    
    def evaluate(self):
        super().evaluate()
        self.value_eval = FieldRule.matchVersion(self.value)
        self.severity = FieldRule.severity(self.cap_eval and self.len_eval and self.value_eval)


class GenericField(FilenameFieldAB):
    """Generic field concrete class.

    Since some filename fields are optional, this class handles the case of fields
    that are not identifiable with the standard set. In this case the field will be 
    validated for length and capitalization, but not for value. 
    """
    def __init__(self, 
                 value: str,
                 id: int) -> None:
        super().__init__('generic'+str(id), value)
    
    def evaluate(self):
        super().evaluate()
        # No restriction on generic field values
        self.value_eval = True
        self.severity = FieldRule.severity(self.cap_eval and self.len_eval)
        self.severity = FieldRule.severity_lax(self.severity and self.value_eval)


class HlspFileName():
    """HLSP filename validation 
    
    Filenames are composed of fields separated by underscores, except 
    that the last field is really composed of two fields separated by a period. 
    The last part of the last field may also contain a period. Certain fields 
    are further composed of elements, separated by hyphens.

    Filenames must have at least 4 and as many as 9 fields to be valid.
    For valid filenames:
      - The first two and the last two fields are required
      - the third from last (N-2) is always required except when the value of 
        N-1 is 'readme'

    Unless all 9 fields are present, or only 4 are present, it is not possible 
    to determine robustly what the other fields (if present) contain.
    
    Parameters
    ----------
    path : str
        Filesystem path relative to the root of the HLSP collection files
    filename : str
        Filename of a collection product
    hlsp_name : str
        Official abbreviation/acronym/initialism of this HLSP collection

    Raises
    ------
    ValueError
        If the number of fields falls outside the limits.
    """
    def __init__(self, 
                 filepath: Path,
                 hlsp_name: str
                 ) -> None:
        self.filepath = filepath
        self.hlspName = hlsp_name
        #self.length = len(self.name)
        self.fields = []
    
    def partition(self) -> None:
        """Partition the filepath into path+filename, and filename into fields
        """
        self.name = self.filepath.name
        self.path = str(self.filepath.parents[0])
        parts = self.name.split('_')
        # split the last part into the product type and the file extension
        last = parts[-1].split('.',1)
        self.fieldvals = parts[:-1] + last
        self.nFields = len(self.fieldvals)
        if self.nFields < 4:
            raise ValueError(f'Filename {self.name} has less than 4 fields')
        elif self.nFields > 9:
            raise ValueError(f'Filename {self.name} has more than 9 fields')
    
    def create_fields(self) -> None:
        """Create Field objects for each field in the filename. 
        """
        nf = self.nFields
        # The first two fields are: 'hslp' and the acronnym of the collection
        self.fields.append(HlspField(self.fieldvals[0]))
        self.fields.append(HlspNameField(self.fieldvals[1], self.hlspName))
        # The last two fields are: the file semantic type and the extension
        self.fields.append(ExtensionField(self.fieldvals[nf-1]))
        self.fields.append(ProductField(self.fieldvals[nf-2]))
        # Files should have a version field unless the product_type is readme
        if self.fieldvals[nf-2].lower() not in ['readme']:
            self.fields.append(VersionField(self.fieldvals[nf-3]))
        # If there are 9 fields, assume the rest of the fields are present in order
        if nf == 9:
            self.fields.append(MissionField(self.fieldvals[2]))
            self.fields.append(InstrumentField(self.fieldvals[3]))
            self.fields.append(TargetField(self.fieldvals[4]))
            self.fields.append(FilterField(self.fieldvals[5]))
        
        # If there are 5 < nFields < 9, the other fields are treated as generic
        elif 5 < nf < 9:
            #print('Creating generic fields')
            for i in range(2,nf-3):
                self.fields.append(GenericField(self.fieldvals[i], i-1))
        # Announce the successful end
        #print(f'Created {nf} fields for file {self.name}')
    
    def evaluate_fields(self):
        """Evaluate attributes of each field
        
        Returns:
        --------
        List of result dictionaries for each field
        """
        for f in self.fields:
            f.evaluate()
        # If the field evaluations succeeded, set a positive status
        self.field_status = 'pass'
        return [f.get_scores() for f in self.fields]

    def evaluate_filename(self):
        """Evaluate attributes of the filename
        
        Returns:
        --------
        Dictionary of file name attributes
        """
        field_status = [f.severity for f in self.fields]
        if 'fatal' in field_status:
            status = 'fail'
        else:
            status = SCORE[FieldRule.capitalization(self.path)]
        attr = {
            'path': self.path,
            'filename': self.name,
            'n_elements': self.nFields,
            'status': status
        }
        return attr
