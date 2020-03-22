# -*- coding: utf-8 -*-
# MySQL Workbench Python script
# <description>
# Written in MySQL Workbench 6.2.3

import grt
import re
from collections import defaultdict

VERSION = '0.3'

TAB = " "*4
PEP8_LIMIT = 120

AVAILABLE_TYPES = [
    'BIGINT', 'BINARY', 'BIT', 'BLOB', 'BOOLEAN', 'CHAR', 'DATE', 'DATETIME', 'DECIMAL',
    'DECIMAL', 'DOUBLE', 'ENUM', 'FLOAT', 'INTEGER', 'LONGBLOB', 'LONGTEXT', 'MEDIUMBLOB',
    'MEDIUMINT', 'MEDIUMTEXT', 'NCHAR', 'NUMERIC', 'NVARCHAR', 'REAL', 'SET', 'SMALLINT',
    'TEXT', 'TIME', 'TIMESTAMP', 'TINYBLOB', 'TINYINT', 'TINYTEXT', 'VARBINARY', 'VARCHAR',
    'YEAR']


def camelize(string):
    """Camelize

    This function will transform a string in a camelized string.
     eg: sOmEtHiNg_hErE -> SomethingHere

    Arguments:
        string {str} -- The string to camelize

    Returns:
        str -- The camelized string
    """
    return re.sub(r"(?:^|_)(.)", lambda x: x.group(0)[-1].upper(), string.lower())


def functionalize(string):
    """Functionalize

    This function will return a functionalized string. It's essentially a camelized string with the first char as a lowercase
     eg: sOmEtHiNg_hErE -> somethingHere

    Arguments:
        string {str} -- The string to functionalize

    Returns:
        str -- The functionalized string
    """
    return string[0].lower() + camelize(string)[1:]


def quote(string):
    """Quote

    This function will quote a string:
     eg: A String -> "A String"

    Arguments:
        string {str} -- The string to quote

    Returns:
        str -- The quoted string
    """
    return '"{string}"'.format(string=string.replace('"', '\\"'))


def endsWith(string, all):
    """endsWith

    This function will tell you if a word ends with one of the provided endings

    Arguments:
        string {str} -- The string to test
        all {set<str>} -- A set of all possible endings

    Returns:
        bool -- True if one of the ending matches, False otherwise
    """
    string = string.lower()
    for i in all:
        if string.endswith(i):
            return True
    return False


def singular(string):
    """Singular

    This function will return the singular version of a string.
     eg: Parties -> Party, Indices -> Index etc...

    Arguments:
        string {str} -- The string to singularise

    Returns:
        str -- The singular string
    """
    if endsWith(string, ('indices', 'indexes')):
        string = string[:-4] + 'ex'
    elif endsWith(string, ('suffixes',)):
        string = string[:-3] + 'x'
    elif endsWith(string, ('aliases', 'dresses')):
        string = string[:-2]
    elif string.endswith('ies'):
        string = string[:-3] + 'y'
    elif string.endswith('s'):
        string = string[:-1]
    return string


def pep8_list(data, tab='', first_row_pad=0):
    """pep8_list

    This function will render a list taking into account overall tab indent and an eventual first row pad.

    Arguments:
        data {list<str>} -- The list to pep8 render

    Keyword Arguments:
        tab {str} -- The overall tab value to prepend to every line (default: {''})
        first_row_pad {number} -- The pad for the first row (default: {0})

    Returns:
        list<str> -- The list formatted to pep8
    """
    value = []
    temp = []
    for a in data:
        temp.append(a)
        pad = 0 if len(value) else first_row_pad
        if len(tab + ', '.join(temp)) >= PEP8_LIMIT - pad:
            value.append(tab + ', '.join(temp[:-1] if len(temp) > 1 else [temp[0]]) + ',')
            temp = [temp[-1]] if len(temp) > 1 else []

    if len(temp):
        value.append(tab + ', '.join(temp))

    return value


def options(string):
    """Options

    This function will read a tring and give you a dict of options based on this formatting:
     eg: option1=a,options2=b -> { 'option1': a, 'option2': 'b' }

    Arguments:
        string {str} -- The string to extract options from

    Returns:
        dict<str:str> -- The dict representing these options
    """
    return dict([t.split('=') for t in string.replace('“', '"').replace('”', '"').split(',') if '=' in t])


class AttributeObject(object):

    def __init__(self, name, classname):
        self.name = name
        self.classname = classname
        self.comment = None
        self.args = []
        self.kwargs = {}
        self.tab = ''

    def __str__(self):
        name = "%s = " % self.name if self.name else ''
        comment = '' if not self.comment else '  # %s' % self.comment
        # simple case
        if not len(self.args) and not len(self.kwargs):
            return self.tab + "{name}{classname}(){comment}".format(
                name=name,
                classname=self.classname,
                comment=comment
            )

        # condensed
        arguments = ", ".join(self.args)
        if len(self.args) and len(self.kwargs):
            arguments += ', '
        if len(self.kwargs):
            arguments += ", ".join(['%s=%s' % item for item in self.kwargs.items()])
        value = self.tab + "{name}{classname}({arguments}){comment}".format(
            name=name,
            classname=self.classname,
            arguments=arguments,
            comment=comment
        )
        if len(value) < PEP8_LIMIT:
            return value

        value = []
        value.append(self.tab + "{name}{classname}({comment}".format(
            name=name,
            classname=self.classname,
            comment=comment
        ))

        value.extend(pep8_list(
            self.args + ['%s=%s' % item for item in self.kwargs.items()],
            self.tab + TAB
        ))
        value.append(self.tab + ')')

        return '\n'.join(value)


class SqlaType(object):

    SQLALCHEMY_TYPESMAP = {
        'Varchar': 'String',
        'Text': 'String',
        'Tinyint': 'Integer',
        'Bigint': 'Integer',
        'Timestamp': 'DateTime',
        'Datetime': 'DateTime',
        'Double': 'Float',
        'Blob': 'Binary',
        'Longblob': 'Binary',
    }

    RAW_TYPE_MAP = {
        'BOOL': 'BOOLEAN',
        'BOOLEAN': 'BOOLEAN',
    }

    TYPE_MAP = {
        'INT': 'INTEGER',
    }

    IMPORT_DATETIME = False
    IMPORT_UNIQUE_CONSTRAINT = False
    MIXINS = set()

    def __init__(self):
        self.sqla = set()
        self.mysql = set()

    def get(self, column):
        column_type = column.formattedType
        if column.formattedRawType in SqlaType.RAW_TYPE_MAP:
            column_type = SqlaType.RAW_TYPE_MAP[column.formattedRawType]

        column_type = re.match(r'(?P<type>[^\(\)]+)(\((?P<size>[^\(\)]+)\))?', column_type).groupdict()
        column_type, size = (column_type['type'].upper(), column_type['size'])
        column_type = SqlaType.TYPE_MAP.get(column_type, column_type).upper()

        assert column_type in AVAILABLE_TYPES

        self.mysql.add(column_type)

        sqla = camelize(column_type)
        sqla = SqlaType.SQLALCHEMY_TYPESMAP.get(sqla, sqla)
        self.sqla.add(sqla if sqla == 'Integer' else "%s as %s" % (sqla, column_type))

        column_type_obj = AttributeObject(None, column_type)
        if 'UNSIGNED' in column.flags and 'INT' in column_type:
            column_type_obj.kwargs['unsigned'] = 'True'

        if size and 'INT' not in column_type.upper():
            column_type_obj.args.append(size)

        return str(column_type_obj).replace('()', '')


class ColumnObject(object):

    def __init__(self, column, index=False, primary=False, unique=False):
        self._column = column
        self.index = index
        self.primary = primary
        self.unique = unique
        self.foreign_key = None

        self.options = options(column.comment)
        self.column_type = USED_TYPES.get(self._column)
        self.name = self.options.get('alias', column.name)

        primary_keys = len([1
                            for i in column.owner.indices
                            for c in i.columns if i.indexType == 'PRIMARY'])

        if self.primary and primary_keys == 1 and self.name != 'id':
            self.name = 'id'

        if self._column.defaultValue and 'CURRENT_TIMESTAMP' in self._column.defaultValue:
            USED_TYPES.IMPORT_DATETIME = True

    def setForeignKey(self, foreign_key):
        self.foreign_key = foreign_key

    def to_print(self):
        return self.options.get('toprint', 'True' if self.primary else 'False') == 'True'

    def getBackref(self):
        if not self.foreign_key:
            return None

        fktable = self.foreign_key.referencedColumns[0].owner.name
        fkname = self.options.get('fkname', functionalize(singular(fktable)))
        fktable = camelize(fktable)
        backrefname = functionalize(self._column.owner.name)

        if self.options.get('relation', True) == 'False':
            return TAB + "# relation for %s.ForeignKey ignored as configured in column comment" % self.name

        attr = AttributeObject(fkname, 'relationship')
        attr.tab = TAB

        attr.args.append(quote(singular(fktable)))

        attr.kwargs['foreign_keys'] = '[{name}]'.format(name=self.name)

        if self.options.get('backref', True) != 'False':
            backref = AttributeObject(None, 'backref')

            backref.args.append(quote(
                self.options.get('backrefname', backrefname)
            ))

            if self.options.get('backrefuselist', True) == 'False':
                backref.kwargs['uselist'] = 'False'

            attr.kwargs['backref'] = backref.args[0] if len(backref.args) + len(backref.kwargs) == 1 else str(backref)

        if self.options.get('uselist', True) == 'False':
            attr.kwargs['uselist'] = 'False'

        if self.options.get('remote_side', None):
            attr.kwargs['remote_side'] = '[%s]' % self.options.get('remote_side', None)
        return str(attr)

    def __str__(self):
        attr = AttributeObject(self.name, 'Column')
        attr.tab = TAB

        if self.name != self._column.name:
            attr.args.append(quote(self._column.name))
        attr.args.append(self.column_type)

        if self.foreign_key:
            fk = AttributeObject(None, 'ForeignKey')

            fk.args.append(quote("%s.%s" % (
                self.foreign_key.referencedColumns[0].owner.name,
                self.foreign_key.referencedColumns[0].name
            )))

            fk.kwargs['name'] = quote(self.foreign_key.name)
            if self.options.get('use_alter', False) == 'True':
                fk.kwargs['use_alter'] = 'True'
            if self.foreign_key.deleteRule and self.foreign_key.deleteRule != "NO ACTION":
                fk.kwargs['ondelete'] = quote(self.foreign_key.deleteRule)
            if self.foreign_key.updateRule and self.foreign_key.updateRule != "NO ACTION":
                fk.kwargs['onupdate'] = quote(self.foreign_key.updateRule)

            attr.args.append(str(fk))

        if self._column.isNotNull == 1:
            attr.kwargs['nullable'] = False
        if self._column.autoIncrement == 1:
            attr.kwargs['autoincrement'] = True
        if self.primary and self._column.autoIncrement != 1:
            attr.kwargs['autoincrement'] = False
        if self.primary:
            attr.kwargs['primary_key'] = True
        if self.unique:
            attr.kwargs['unique'] = True
        if self.index:
            attr.kwargs['index'] = True
        if self._column.defaultValue:
            default = self._column.defaultValue
            onupdate = None
            if "ON UPDATE" in default:
                onupdate = default.split('ON UPDATE')[1].strip()
                default = default.split('ON UPDATE')[0].strip()
            if 'CURRENT_TIMESTAMP' in default:
                default = 'datetime.datetime.utcnow'
            if onupdate and 'CURRENT_TIMESTAMP' in onupdate:
                onupdate = 'datetime.datetime.utcnow'
            attr.kwargs['default'] = default
            if onupdate:
                attr.kwargs['onupdate'] = onupdate
        if self.name == 'id':
            attr.comment = 'pylint: disable=invalid-name'

        return str(attr)


class TableObject(object):

    def __init__(self, table):
        self._table = table
        self.name = singular(camelize(table.name))

        self.options = options(table.comment)
        self.comments = []
        self.table_args = {}
        self.columns = []

        self.indices = defaultdict(set)
        self.uniques_multi = defaultdict(set)

        for index in self._table.indices:
            columns = [c.referencedColumn.name for c in index.columns]
            if index.indexType == 'UNIQUE' and len(index.columns) > 1:
                self.uniques_multi[index.name].update(columns)
            self.indices[index.indexType].update(columns)

        if len(self.uniques_multi):
            USED_TYPES.IMPORT_UNIQUE_CONSTRAINT = True

        if 'mixins' in self.options:
            USED_TYPES.MIXINS.update(self.options['mixins'].split(','))

        self._setTableArgs()
        self._setColumns()

    def _setTableArgs(self):
        if self._table.tableEngine:
            self.table_args['mysql_engine'] = self._table.tableEngine

        charset = self._table.defaultCharacterSetName or self._table.owner.defaultCharacterSetName
        if charset:
            self.table_args['mysql_charset'] = charset

        if sum([column.autoIncrement for column in self._table.columns]) > 0:
            self.table_args['sqlite_autoincrement'] = True

    def _setColumns(self):
        for column in self._table.columns:
            self.columns.append(ColumnObject(
                column,
                index=column.name in self.indices.get('INDEX', []),
                primary=column.name in self.indices.get('PRIMARY', []),
                unique=column.name in self.indices.get('UNIQUE', [])
                and column.name not in [c for clist in self.uniques_multi.values()
                                        for c in clist]
            ))

        # link columns together with foreign keys
        for foreign_key in self._table.foreignKeys:
            if len(foreign_key.referencedColumns) > 1:
                self.comments.append('Foreign Key ignored')
                continue

            self.getColumn(foreign_key.columns[0].name).setForeignKey(foreign_key)

    def getColumn(self, name):
        for column in self.columns:
            if column.name == name:
                return column
            if column._column.name == name:
                return column
        return None

    def __str__(self):
        value = []

        inherits_from = ['object' if self.options.get('abstract', 'False') == 'True' else 'DECLARATIVE_BASE']
        if 'mixins' in self.options:
            inherits_from.extend(self.options['mixins'].split(','))
        value.append("class %s(%s):" % (
            self.name,
            ', '.join(inherits_from)
        ))
        for comment in self.comments:
            value.append(TAB + '# %s' % comment)
        value.append("")
        if 'abstract' not in self._table.comment:
            value.append(TAB + "__tablename__ = '%s'" % self._table.name)

        value.append(TAB + "__table_args__ = (")
        for index_name, columns in self.uniques_multi.items():
            attr = AttributeObject(None, 'UniqueConstraint')
            attr.tab = TAB * 2
            attr.args.append(quote(quote(', ').join(columns)).replace('\\', ''))
            attr.kwargs['name'] = quote(index_name)
            value.append(str(attr) + ',')
        value.append(TAB * 2 + "%s" % self.table_args)
        value.append(TAB + ")")

        value.append('')
        value.extend([str(c) for c in self.columns])
        value.append('')

        relations = [br for br in [c.getBackref() for c in self.columns] if br is not None]
        value.extend(relations)

        if len(relations):
            value.append('')

        value.append(TAB + 'def __repr__(self):')
        value.append(TAB * 2 + 'return self.__str__()')
        value.append('')
        value.append(TAB + 'def __str__(self):')
        attr = AttributeObject(None, self.name)
        attr.args = ['%%(%s)s' % c.name for c in self.columns if c.to_print()]
        value.append(TAB * 2 + 'return "<%s>" %% self.__dict__' % str(attr))

        return '\n'.join(value)


USED_TYPES = SqlaType()

def generateExport():
    tables = []
    for table in grt.root.wb.doc.physicalModels[0].catalog.schemata[0].tables:
        print(" -> Working on %s" % table.name)
        tables.append(TableObject(table))

    export = []
    export.append('"""')
    export.append('This file has been automatically generated with workbench_alchemy v%s' % VERSION)
    export.append('For more details please check here:')
    export.append('https://github.com/PiTiLeZarD/workbench_alchemy')
    export.append('"""')


    def append_types(types, from_import, tab=TAB):
        lines = []
        if not len(types):
            return lines
        from_import = "from %s import" % from_import
        types = pep8_list(types, first_row_pad=len(tab) + len(from_import))
        lines.append(tab + "%s %s" % (from_import, types[0]))
        if len(types) > 1:
            lines[-1] += ' \\'
        for index in range(1, len(types)):
            lines.append(tab * 2 + types[index])
            if index < len(types) - 1:
                lines[-1] += ' \\'
        return lines

    export.append("")
    export.append("import os")
    if USED_TYPES.IMPORT_DATETIME:
        export.append("import datetime")
    export.append("from sqlalchemy.orm import relationship")
    export.append("from sqlalchemy import Column, ForeignKey")
    if USED_TYPES.IMPORT_UNIQUE_CONSTRAINT:
        export.append("from sqlalchemy.schema import UniqueConstraint")
    export.append("from sqlalchemy.ext.declarative import declarative_base")
    if len(USED_TYPES.MIXINS):
        export = export + append_types(USED_TYPES.MIXINS, '.mixins', tab='')
    export.append("")


    export.append("if os.environ.get('DB_TYPE', 'MySQL') == 'MySQL':")
    export = export + append_types(USED_TYPES.mysql, 'sqlalchemy.dialects.mysql')
    export.append("else:")
    export = export + append_types(USED_TYPES.sqla, 'sqlalchemy')
    if 'Integer' in USED_TYPES.sqla:
        export.append("")
        export.append("    class INTEGER(Integer):")
        export.append("        def __init__(self, *args, **kwargs):")
        export.append("            super(Integer, self).__init__()  # pylint: disable=bad-super-call")
        export.append("")

        if 'TINYINT' in USED_TYPES.mysql:
            export.append("    TINYINT = INTEGER")

        if 'BIGINT' in USED_TYPES.mysql:
            export.append("    BIGINT = INTEGER")

    export.append("")
    export.append("DECLARATIVE_BASE = declarative_base()")
    export.append("")

    for table in tables:
        export.append("")
        export.append(str(table))
        export.append("")

    return export

def copyExportToClipboard(export):
    grt.modules.Workbench.copyToClipboard('\n'.join(export))
    print("-" * 20)
    print("-- SQLAlchemy export v%s" % VERSION)
    print("-" * 20)
    print("Copied to clipboard")


if __name__ == '__main__':
    copyExportToClipboard(generateExport())
