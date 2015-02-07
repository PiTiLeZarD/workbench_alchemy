# -*- coding: utf-8 -*-
# MySQL Workbench Python script
# <description>
# Written in MySQL Workbench 6.2.3

import grt
import re

VERSION = '0.2.1'

USE_MYSQL_TYPES = True
TAB = "    "
PEP8_LIMIT = 120

TYPES = {
    'sqla': [],
    'sqla_alt': [],
    'mysql': [],
}
TYPESMAP = {
    'INT': 'INTEGER',
}
SQLALCHEMY_TYPESMAP = {
    'Varchar': 'String',
    'Text': 'String',
    'Tinyint': 'Integer',
    'Timestamp': 'DateTime',
    'Datetime': 'DateTime',
    'Double': 'Float',
    'Blob': 'String',
}
MYSQLTYPES = [
    'BIGINT', 'BINARY', 'BIT', 'BLOB', 'BOOLEAN', 'CHAR', 'DATE', 'DATETIME', 'DECIMAL',
    'DECIMAL', 'DOUBLE', 'ENUM', 'FLOAT', 'INTEGER', 'LONGBLOB', 'LONGTEXT', 'MEDIUMBLOB',
    'MEDIUMINT', 'MEDIUMTEXT', 'NCHAR', 'NUMERIC', 'NVARCHAR', 'REAL', 'SET', 'SMALLINT',
    'TEXT', 'TIME', 'TIMESTAMP', 'TINYBLOB', 'TINYINT', 'TINYTEXT', 'VARBINARY', 'VARCHAR',
    'YEAR']


def camelize(name):
    return re.sub(r"(?:^|_)(.)", lambda x: x.group(0)[-1].upper(), name)


def functionalize(name):
    return name[0].lower() + camelize(name)[1:]


def quote(s):
    return '"%s"' % s


def endsWith(name, all):
    name = name.lower()
    for i in all:
        if name.endswith(i):
            return True
    return False


def singular(name):
    if endsWith(name, ('indices',)):
        name = name[:-4] + 'ex'
    elif endsWith(name, ('suffixes',)):
        name = name[:-3] + 'x'
    elif endsWith(name, ('aliases', 'dresses')):
        name = name[:-2]
    elif name.endswith('ies'):
        name = name[:-3] + 'y'
    elif name.endswith('s'):
        name = name[:-1]
    return name


def pep8_list(data, tab='', first_row_pad=0):
    value = []
    temp = []
    for a in data:
        temp.append(a)
        pad = 0 if len(value) else first_row_pad
        if len(tab + ', '.join(temp)) >= PEP8_LIMIT - pad:
            value.append(tab + ', '.join(temp[:-1]) + ',')
            temp = [temp[-1]]

    if len(temp):
        value.append(tab + ', '.join(temp))

    return value


class AttributeObject(object):
    def __init__(self, name, classname):
        self.name = name
        self.classname = classname
        self.pylint_message = None
        self.args = []
        self.kwargs = {}
        self.tab = ''

    def __str__(self):
        name = "%s = " % self.name if self.name else ''
        # simple case
        if not len(self.args) and not len(self.kwargs):
            return self.tab + "%s%s()%s" % (name, self.classname, self.pylint_message or '')

        # condensed
        arguments = ", ".join(self.args)
        if len(self.kwargs):
            arguments += ', ' + ", ".join(['%s=%s' % item for item in self.kwargs.items()])
        value = self.tab + "%s%s(%s)%s" % (name, self.classname, arguments, self.pylint_message or '')
        if len(value) < PEP8_LIMIT:
            return value

        value = []
        value.append(self.tab + "%s%s(%s" % (name, self.classname, self.pylint_message or ''))

        value.extend(pep8_list(
            self.args + ['%s=%s' % item for item in self.kwargs.items()],
            self.tab + TAB
        ))
        value.append(self.tab + ')')

        return '\n'.join(value)


def getType(column):
    column_type = column.formattedType
    if column.formattedRawType in ('BOOLEAN', 'BOOL'):
        column_type = 'BOOLEAN'
    column_type = re.match(r'(?P<type>[^\(\)]+)(\((?P<size>[^\(\)]+)\))?', column_type).groupdict()
    column_type, size = (column_type['type'], column_type['size'])
    column_type = TYPESMAP.get(column_type.upper(), column_type).upper()

    if USE_MYSQL_TYPES and column_type in MYSQLTYPES:
        # case of mysql TYPES
        column_type = column_type.upper()
        if column_type not in TYPES['mysql']:
            TYPES['mysql'].append(column_type)

            sqla = camelize(column_type.lower())
            sqla = SQLALCHEMY_TYPESMAP.get(sqla, sqla)
            TYPES['sqla_alt'].append("%s as %s" % (sqla, column_type))

        if 'UNSIGNED' in column.flags and 'INT' in column_type:
            column_type = '%s(unsigned=True)' % column_type

    else:
        # sqlalchemy TYPES
        column_type = camelize(column_type.lower())
        column_type = SQLALCHEMY_TYPESMAP.get(column_type, column_type)
        if column_type not in TYPES['sqla']:
            TYPES['sqla'].append(column_type)

    if size and 'INT' not in column_type.upper():
        column_type = '%s(%s)' % (column_type, size)

    return column_type


class ColumnObject(object):

    def __init__(self, column, table_obj):
        self._column = column
        self.table_obj = table_obj
        self.name = column.name

        self.options = {}
        self.column_type = None
        self.features = {}
        self.foreign_key = None

        self.build()

    def build(self):
        self._setType()
        self._setOptions()
        self._setFeatures()
        self._setForeignKey()

    def _setType(self):
        self.column_type = getType(self._column)

    def _setOptions(self):
        if self._column.comment:
            self.options = dict([t.split('=') for t in self._column.comment.split(',') if '=' in t])

        self.name = self.options.get('alias', self.name)

    def _setFeatures(self):
        if self._column.isNotNull == 1:
            self.features['nullable'] = False
        if self._column.autoIncrement == 1:
            self.features['autoincrement'] = True

        if self._column.name in self.table_obj.indices['PRIMARY']:
            self.features['primary_key'] = True
            if (len(self.table_obj.indices['PRIMARY']) == 1) and self.name != 'id':
                self.name = 'id'
            elif self._column.autoIncrement != 1:
                self.features['autoincrement'] = False
        if self._column.name in self.table_obj.indices['INDEX']:
            self.features['index'] = True
        if self._column.name in [i[1][0] for i in self.table_obj.indices['UNIQUE'] if len(i[1]) == 1]:
            self.features['unique'] = True

        if self._column.defaultValue:
            self.features['default'] = self._column.defaultValue

    def _setForeignKey(self):
        foreign_key = self.table_obj.foreign_keys.get(self._column.name, None)
        if foreign_key:
            fkcol, fktable, ondelete, onupdate = foreign_key
            attr = AttributeObject(None, 'ForeignKey')
            attr.args.append(quote(fkcol))
            if ondelete:
                attr.kwargs['ondelete'] = quote(ondelete)
            if onupdate:
                attr.kwargs['onupdate'] = quote(onupdate)

            self.foreign_key = str(attr)

    def __str__(self):
        attr = AttributeObject(self.name, 'Column')
        attr.tab = TAB

        if self.name == 'id':
            attr.pylint_message = '  # pylint: disable=invalid-name'

        if self.name != self._column.name:
            attr.args.append(quote(self._column.name))

        attr.args.append(self.column_type)

        if self.foreign_key:
            attr.args.append(self.foreign_key)

        attr.kwargs = self.features

        return str(attr)


class TableObject(object):

    def __init__(self, table):
        self._table = table
        self.name = singular(camelize(table.name))

        self.comments = []
        self.table_args = {}
        self.uniques = {}
        self.options = {}
        self.indices = {'PRIMARY': [], 'INDEX': [], 'UNIQUE': {}, 'UNIQUE_MULTI': {}}
        self.foreign_keys = {}
        self.columns = []
        self.relations = []
        self.columns_to_print = set()

        self.build()

    def build(self):
        self._setTableArgs()
        self._setIndices()
        self._setUniques()
        self._setForeignKeys()
        self._setColumns()
        self._setRelations()
        self._setColumnsToPrint()

    def _setTableArgs(self):
        if self._table.tableEngine:
            self.table_args['mysql_engine'] = self._table.tableEngine

        charset = self._table.defaultCharacterSetName or self._table.owner.defaultCharacterSetName
        if charset:
            self.table_args['mysql_charset'] = charset

        if sum([column.autoIncrement for column in self._table.columns]) > 0:
            self.table_args['sqlite_autoincrement'] = True

    def _setUniques(self):
        uniques_multi = [i for i in self.indices['UNIQUE'] if len(i[1]) > 1]
        if not len(uniques_multi):
            return

        for index_name, columns in uniques_multi:
            self.indices['UNIQUE_MULTI'][index_name] = columns

    def _setIndices(self):
        for index in self._table.indices:
            if index.indexType == 'PRIMARY':
                self.indices['PRIMARY'] += [c.referencedColumn.name for c in index.columns]
            if index.indexType == 'INDEX':
                self.indices['INDEX'] += [c.referencedColumn.name for c in index.columns]
            if index.indexType == 'UNIQUE':
                if len(index.columns) > 1:
                    self.indices['UNIQUE_MULTI'][index.name] = [c.referencedColumn.name for c in index.columns]
                else:
                    self.indices['UNIQUE'].update(
                        dict([([c.referencedColumn.name for c in index.columns][0], index.name)])
                    )

    def _setForeignKeys(self):
        for fk in self._table.foreignKeys:
            if len(fk.referencedColumns) > 1:
                # I don't even think that sqlalchemy handles multi column foreign keys...
                self.comments.append('multicolumns foreign key ignored')
                continue

            for i in range(0, len(fk.referencedColumns)):
                relation = '%s.%s' % (fk.referencedColumns[i].owner.name, fk.referencedColumns[i].name)
                fktable = camelize(fk.referencedColumns[i].owner.name)
                ondelete = onupdate = None
                if fk.deleteRule and fk.deleteRule != "NO ACTION":
                    ondelete = fk.deleteRule
                if fk.updateRule and fk.updateRule != "NO ACTION":
                    onupdate = fk.updateRule
                self.foreign_keys[fk.columns[i].name] = (relation, fktable, ondelete, onupdate)

    def _setColumns(self):
        for column in self._table.columns:
            self.columns.append(ColumnObject(column, self))

    def getColumn(self, name):
        for column in self.columns:
            if column.name == name:
                return column
            if column._column.name == name:
                return column
        return None

    def _setRelations(self):
        if 'norelations' in self._table.comment:
            self.comments.append("relations ignored for this table")
            return

        for column_name, v in self.foreign_keys.items():
            column = self.getColumn(column_name)
            fkcol, fktable, ondelete, onupdate = v
            fkname = column.options.get('fkname', functionalize(singular(fktable)))

            if column.options.get('relation', True) == 'False':
                self.comments.append("relation <%s> ignored for this table" % fkname)
                continue

            backrefname = None
            remote_side = None
            if column.options.get('backref', True) != 'False':
                backrefname = column.options.get('backrefname', functionalize(self._table.name))
                remote_side = column.options.get('remote_side', None)

            self.relations.append((
                fkname, singular(fktable), column.name, backrefname, remote_side
            ))

    def _setColumnsToPrint(self):
        for column in [self.getColumn(name) for name in self.indices['PRIMARY']]:
            if column.options.get('toprint', False) == 'False':
                continue
            self.columns_to_print.add(column.name)
        for column in self.columns:
            if column.options.get('toprint', False) == 'True':
                self.columns_to_print.add(column.name)

    def __str__(self):
        value = []

        value.append("class %s(%s):" % (
            self.name,
            'object' if 'abstract' in self._table.comment else 'DECLARATIVE_BASE'
        ))
        for comment in self.comments:
            value.append(TAB + '# %s' % comment)
        value.append("")
        if 'abstract' not in self._table.comment:
            value.append(TAB + "__tablename__ = '%s'" % self._table.name)

        value.append(TAB + "__table_args__ = (")
        for index_name, columns in self.indices['UNIQUE_MULTI'].items():
            value.append(TAB * 2 + "UniqueConstraint('%s', name='%s')," % ("', '".join(columns), index_name))
        value.append(TAB * 2 + "%s" % self.table_args)
        value.append(TAB + ")")

        value.append('')
        value.extend([str(c) for c in self.columns])
        value.append('')

        for fkname, fktable, column_name, backrefname, remote_side in self.relations:
            attr = AttributeObject(fkname, 'relationship')
            attr.tab = TAB
            attr.args.append(quote(singular(fktable)))
            attr.kwargs['foreign_keys'] = '[%s]' % column_name
            if backrefname:
                attr.kwargs['backref'] = quote(backrefname)
            if remote_side:
                attr.kwargs['remote_side'] = '[%s]' % remote_side
            value.append(str(attr))

        if len(self.relations):
            value.append('')

        value.append(TAB + 'def __repr__(self):')
        value.append(TAB * 2 + 'return self.__str__()')
        value.append('')
        value.append(TAB + 'def __str__(self):')
        attr = AttributeObject(None, self.name)
        attr.args = ['%%(%s)s' % name for name in self.columns_to_print]
        value.append(TAB * 2 + 'return "<%s>" %% self.__dict__' % str(attr))

        return '\n'.join(value)


tables = []
for table in grt.root.wb.doc.physicalModels[0].catalog.schemata[0].tables:
    print " -> Working on %s" % table.name
    tables.append(TableObject(table))

export = []
export.append('"""')
export.append('This file has been automatically generated with workbench_alchemy v%s' % VERSION)
export.append('For more details please check here:')
export.append('https://github.com/PiTiLeZarD/workbench_alchemy')
export.append('"""')

export.append("")
export.append("USE_MYSQL_TYPES = %s" % USE_MYSQL_TYPES)
export.append("try:")
export.append("    from . import USE_MYSQL_TYPES")
export.append("except:")
export.append("    pass")
export.append("")
export.append("")
export.append("from sqlalchemy.orm import relationship")
export.append("from sqlalchemy import Column, ForeignKey")
if len([1 for t in tables if len(t.indices['UNIQUE_MULTI'])]):
    export.append("from sqlalchemy.schema import UniqueConstraint")
export.append("from sqlalchemy.ext.declarative import declarative_base")
if len(TYPES['sqla']):
    export.append("from sqlalchemy import %s" % ', '.join(TYPES['sqla']))
export.append("")
export.append("if USE_MYSQL_TYPES:")
if len(TYPES['mysql']):
    types = pep8_list(TYPES['mysql'], first_row_pad=37+len(TAB))
    export.append(TAB + "from sqlalchemy.dialects.mysql import %s" % types[0])
    if len(types) > 1:
        export[-1] += ' \\'
    for index in range(1, len(types)):
        export.append(TAB * 2 + types[index])
        if index < len(types) - 1:
            export[-1] += ' \\'
export.append("else:")
if len(TYPES['sqla_alt']):
    types = pep8_list(TYPES['sqla_alt'], first_row_pad=22+len(TAB))
    export.append(TAB + "from sqlalchemy import %s" % types[0])
    if len(types) > 1:
        export[-1] += ' \\'
    for index in range(1, len(types)):
        export.append(TAB * 2 + types[index])
        if index < len(types) - 1:
            export[-1] += ' \\'
export.append("")
export.append("DECLARATIVE_BASE = declarative_base()")
export.append("")

for table in tables:
    export.append("")
    export.append(str(table))
    export.append("")

grt.modules.Workbench.copyToClipboard('\n'.join(export))
print "-" * 20
print "-- SQLAlchemy export v%s" % VERSION
print "-" * 20
print "Copied to clipboard"
