from mock import MagicMock

root = MagicMock()
modules = MagicMock()


def get_grt_foreignKey(fk_name, columns=[], referencedColumns=[], deleteRule='NO ACTION', updateRule='SET NULL'):
    fk = MagicMock(
        columns=columns,
        referencedColumns=referencedColumns,
        deleteRule=deleteRule,
        updateRule=updateRule
    )
    fk.name = fk_name
    return fk


def get_grt_index(index_type='PRIMARY', columns=[]):
    return MagicMock(
        columns=[MagicMock(referencedColumn=c) for c in columns],
        indexType=index_type
    )


def get_grt_table(table_name, columns=[], indices=[], foreignKeys=[], tableEngine=None, charset='utf8'):
    table = MagicMock(
        tableEngine=tableEngine,
        defaultCharacterSetName=charset,
        columns=columns,
        indices=indices,
        foreignKeys=foreignKeys
    )
    table.name = table_name
    for c in columns:
        c.owner = table
    return table


def get_grt_column(column_name, table_name, sql_type, defaultValue=None, comment=None, isNotNull=0, autoIncrement=0):
    column = MagicMock(
        owner=get_grt_table(table_name),
        defaultValue=defaultValue,
        formattedType=sql_type,
        formattedRawType=sql_type,
        isNotNull=isNotNull,
        autoIncrement=autoIncrement
    )
    if comment is not None:
        column.comment = comment
    column.name = column_name
    return column
