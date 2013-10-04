import re

version = '0.6'

types = {
    'sqla': [],
    'mysql': []
}
typesmap = {
    'INT': 'INTEGER',
}
sqlalchemy_typesmap = {
    'Varchar': 'String',
    'Text': 'String',
    'Tinyint': 'Integer',
    'Timestamp': 'DateTime',
    'Datetime': 'DateTime',
}

USE_MYSQL_TYPES = True
mysqltypes = ['BIGINT', 'BINARY', 'BIT', 'BLOB', 'BOOLEAN', 'CHAR', 'DATE', 'DATETIME', 'DECIMAL', 'DECIMAL', 'DOUBLE', 'ENUM', 'FLOAT', 'INTEGER', 'LONGBLOB', 'LONGTEXT', 'MEDIUMBLOB', 'MEDIUMINT', 'MEDIUMTEXT', 'NCHAR', 'NUMERIC', 'NVARCHAR', 'REAL', 'SET', 'SMALLINT', 'TEXT', 'TIME', 'TIMESTAMP', 'TINYBLOB', 'TINYINT', 'TINYTEXT', 'VARBINARY', 'VARCHAR', 'YEAR']

def camelize( name ):
    return re.sub(r"(?:^|_)(.)", lambda x: x.group(0)[-1].upper(), name)

def singular( name ):
    if name.endswith('ices'):
        name = name[:-4] + 'ex'
    if name.endswith('xes'):
        name = name[:-3] + 'x'
    if name.endswith('ies'):
        name = name[:-3] + 'y'
    if name.endswith('ses'):
        name = name[:-2]
    elif name.endswith('s'):
        name = name[:-1]
    return name

def getType( column ):
    column_type = column.formattedType
    column_type = re.match(r'(?P<type>[^\(\)]+)(\((?P<size>[^\(\)]+)\))?', column_type).groupdict()
    column_type, size = (column_type['type'], column_type['size'])
    column_type = typesmap.get(column_type.upper(), column_type).upper()

    if USE_MYSQL_TYPES and column_type in mysqltypes:
        # case of mysql types
        column_type = column_type.upper()
        if column_type not in types['mysql']: types['mysql'].append(column_type)

        if 'UNSIGNED' in column.flags and 'INT' in column_type:
            column_type = '%s(unsigned=True)' % column_type

    else:
        # sqlalchemy types
        column_type = camelize( column_type.lower() )
        column_type = sqlalchemy_typesmap.get(column_type, column_type)
        if column_type not in types['sqla']: types['sqla'].append(column_type)

    if size and 'INT' not in column_type.upper():
        column_type = '%s(%s)' % (column_type, size)

    return column_type

def exportTable( table ):
    export = []
    primary = []
    indices = []
    unique = []

    for index in table.indices:
        for column in index.columns:
            if index.indexType == 'PRIMARY':
                primary.append(column.referencedColumn.name)
            if index.indexType == 'UNIQUE':
                unique.append(column.referencedColumn.name)
            if index.indexType == 'INDEX':
                indices.append(column.referencedColumn.name)

    foreignKeys = {}
    for fk in table.foreignKeys:
        if len(fk.referencedColumns) > 1:
            continue
        for i in range(0, len(fk.referencedColumns)):
            relation = '%s.%s' % (fk.referencedColumns[i].owner.name, fk.referencedColumns[i].name)
            fktable = camelize(fk.referencedColumns[i].owner.name)
            ondelete = onupdate = None
            if fk.deleteRule and fk.deleteRule != "NO ACTION":
                ondelete = fk.deleteRule
            if fk.updateRule and fk.updateRule != "NO ACTION":
                onupdate = fk.updateRule
            foreignKeys[fk.columns[i].name] = (relation, fktable, ondelete, onupdate)

    classname = singular( camelize( table.name ) )

    export.append("class %s(Base):" % classname)
    export.append("  __tablename__ = '%s'" % table.name)
    export.append("  ")

    aliases = {}
    for column in table.columns:
        column_name = column.name
        column_alias = ''
        column_type = getType(column)

        options = []
        if column.name in foreignKeys:
            fkcol, fktable, ondelete, onupdate = foreignKeys[column.name]
            fkopts = []
            if ondelete: fkopts.append('ondelete="%s"' % ondelete)
            if onupdate: fkopts.append('onupdate="%s"' % onupdate)
            fkopts = len(fkopts) and ', ' + ', '.join(fkopts) or ''
            options.append('ForeignKey("%s"%s)' % (fkcol, fkopts))
        if column.isNotNull == 1:
            options.append('nullable=False')
        if column.autoIncrement == 1:
            options.append('autoincrement=True')
        if column.name in primary:
            options.append('primary_key=True')
            if (len(primary) == 1) and (column_name != 'id'):
                aliases[column_name] = 'id'
                column_alias = '"%s", ' % column_name
                column_name = 'id'
            elif column.autoIncrement != 1:
                options.append('autoincrement=False')
        if column.name in indices:
            options.append('index=True')
        if column.name in unique:
            options.append('unique=True')

        if len(options):
            options = ', ' + ', '.join(options)
        else:
            options = ''

        export.append("  %s = Column( %s%s%s )" % (column_name, column_alias, column_type, options))

    export.append("")
    for k, v in foreignKeys.items():
        fkcol, fktable, ondelete, onupdate = v
        attr = singular(fktable)
        attr = attr[0].lower() + attr[1:]

        if 'norelations' in table.comment:
            export.append('  # relationship %s ignored' % attr)
            continue
        
        backref = camelize(table.name)
        backref = backref[0].lower() + backref[1:]
        export.append('  %s = relationship( "%s", foreign_keys=[%s], backref="%s" )' % (attr, singular(fktable), aliases.get(k,k), backref))


    export.append("")
    export.append('  def __repr__( self ):')
    export.append('    return self.__str__()')

    export.append("")

    export.append('  def __str__( self ):')
    export.append("    return '<"+classname+" "+ ' '.join(['%('+i+')s' for i in primary]) +">' % self.__dict__")

    export.append("")
    
    return export

print "-"*20
print "-- SQLAlchemy export v%s" % version
print "-"*20

export = []
export.append('"""')
export.append('This file has been automatically generated with workbench_alchemy v%s' % version)
export.append('For more details please check here:')
export.append('https://github.com/PiTiLeZarD/workbench_alchemy')
export.append('"""')

tables = []
for table in grt.root.wb.doc.physicalModels[0].catalog.schemata[0].tables:
    print " -> Working on %s" % table.name
    tables.extend( exportTable(table) )

export.append("")
export.append("from sqlalchemy.orm import relationship")
export.append("from sqlalchemy import Column, ForeignKey")
if len(types['sqla']): export.append("from sqlalchemy import %s" % ', '.join(types['sqla']))
if len(types['mysql']): export.append("from sqlalchemy.dialects.mysql import %s" % ', '.join(types['mysql']))
export.append("from sqlalchemy.ext.declarative import declarative_base")
export.append("")
export.append("Base = declarative_base()")
export.append("")

export.extend(tables)


grt.modules.Workbench.copyToClipboard('\n'.join(export))
print "Copied to clipboard"

