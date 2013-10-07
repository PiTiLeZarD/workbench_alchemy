import re

version = '0.8'

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

def endsWith( name, all ):
    name = name.lower()

def singular( name ):
    if endsWith(name, ('indices',)):
        name = name[:-4] + 'ex'
    if endsWith(name, ('suffixes',)):
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
    # yeah I know... but I can't prevent myself...
    # this is to convert all column's comments from opt1=value1,opt2=value2
    # to a dict like {column_name: {opt1:value1, opt2:value2} ...}
    options = dict([(c.name, dict([t.split('=') for t in (c.comment or '').split(',') if '=' in t])) for c in table.columns])

    classname = singular( camelize( table.name ) )
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
            # I don't even think that sqlalchemy handles multi column foreign keys...
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


    export.append("class %s(Base):" % classname)
    export.append("  __tablename__ = '%s'" % table.name)
    export.append("  ")

    aliases = {}
    for column in table.columns:
        column_name = column.name
        column_alias = ''
        column_type = getType(column)

        if 'alias' in options[column_name]:
            aliases[column_name] = options[column_name]['alias']

        column_options = []
        column_options.append(column_type)

        if column.name in foreignKeys:
            fkcol, fktable, ondelete, onupdate = foreignKeys[column.name]
            fkopts = []
            if ondelete: fkopts.append('ondelete="%s"' % ondelete)
            if onupdate: fkopts.append('onupdate="%s"' % onupdate)
            fkopts = len(fkopts) and ', ' + ', '.join(fkopts) or ''
            column_options.append('ForeignKey("%s"%s)' % (fkcol, fkopts))
        if column.isNotNull == 1:
            column_options.append('nullable=False')
        if column.autoIncrement == 1:
            column_options.append('autoincrement=True')
        if column.name in primary:
            column_options.append('primary_key=True')
            if (len(primary) == 1) and (column_name != 'id') and (column_name not in aliases):
                aliases[column_name] = 'id'
            elif column.autoIncrement != 1:
                column_options.append('autoincrement=False')
        if column.name in indices:
            column_options.append('index=True')
        if column.name in unique:
            column_options.append('unique=True')

        if column_name in aliases:
            column_options = ['"%s"' % column_name] + column_options
            column_name = aliases[column_name]

        export.append("  %s = Column( %s )" % (column_name, ', '.join(column_options)))

    export.append("")
    for column_name, v in foreignKeys.items():
        fkcol, fktable, ondelete, onupdate = v

        fkname = singular(fktable)
        fkname = fkname[0].lower() + fkname[1:]
        if options[column_name].get('fkname', None) is not None:
            fkname = options[column_name].get('fkname', None)

        if 'norelations' in table.comment:
            export.append('  # relationship %s ignored globally on the table' % fkname)
            continue
        
        if options[column_name].get('relation', True) == 'False':
            export.append('  # relationship %s ignored by column' % fkname)
            continue
        
        backref = ''
        if options[column_name].get('backref', True) != 'False':
            if options[column_name].get('backrefname', None) is not None:
                backref = options[column_name].get('backrefname', None)
            else:
                backref = camelize(table.name)
                backref = backref[0].lower() + backref[1:]

            backref = ', backref="%s"' % backref

        column_name = aliases.get(column_name, column_name)
        export.append('  %s = relationship( "%s", foreign_keys=[%s]%s )' % (fkname, singular(fktable), column_name, backref))


    export.append("")
    export.append('  def __repr__( self ):')
    export.append('    return self.__str__()')

    export.append("")

    # take all column you say or by default the primary ones (unless specified otherwise)
    toprint = [aliases.get(c, c) for c in [p for p, o in options.items() if o.get('toprint', str(p in primary and options[p].get('toprint', True) != 'False')) == 'True']]
    export.append('  def __str__( self ):')
    export.append("    return '<"+classname+" "+ ' '.join(['%('+i+')s' for i in toprint]) +">' % self.__dict__")

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

