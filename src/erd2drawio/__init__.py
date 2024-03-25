from __future__ import annotations

from xml.dom import minidom
import erd2drawio.gen.models as models


class Defaults:
    KEY_WIDTH = 30
    COLUMN_NAME_WIDTH = 150
    HEIGHT = 30


class Styles:
    TABLE = "shape=table;startSize={START_SIZE};container=1;collapsible=1;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;align=center;resizeLast=1;html=1;"
    COLUMN_BASE = "shape=tableRow;horizontal=0;startSize={START_SIZE};swimlaneHead=0;swimlaneBody=0;fillColor=none;collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;top={TOP};left=0;right=0;bottom=0;"
    COLUMN_KEY = "shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;fontStyle=1;overflow=hidden;whiteSpace=wrap;html=1;"
    COLUMN_NAME = "shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;right=0;align=left;spacingLeft=6;fontStyle={FONT_STYLE};overflow=hidden;whiteSpace=wrap;html=1;"
    RELATION_EDGE = "edgeStyle=entityRelationEdgeStyle;fontSize=12;html=1;endArrow={END_ARROW};startArrow={START_ARROW};rounded=0;exitX={FROM};exitY=0.5;exitDx=0;exitDy=0;entryX={TO};entryY=0.5;entryDx=0;entryDy=0;endFill=0;"


class Tags:
    DIAGRAM = "diagram"
    MX_GRAPH_MODEL = "mxGraphModel"
    ROOT = "root"
    MX_FILE = "mxfile"
    MX_CELL = "mxCell"
    MX_GEOMETRY = "mxGeometry"
    MX_RECTANGLE = "mxRectangle"


class RelationshipType:
    def __init__(self, startArrow: str, endArrow: str) -> None:
        self.startArrow = startArrow
        self.endArrow = endArrow

    @staticmethod
    def ONE_ONLY() -> RelationshipType:
        return RelationshipType("ERmandOne", "ERmandOne")

    @staticmethod
    def ONE_MANY() -> RelationshipType:
        return RelationshipType("ERmandOne", "ERoneToMany")

    @staticmethod
    def ZERO_ONLY() -> RelationshipType:
        return RelationshipType("ERmandOne", "ERzeroToOne")

    @staticmethod
    def ZERO_MANY() -> RelationshipType:
        return RelationshipType("ERmandOne", "ERzeroToMany")

    @staticmethod
    def get(relationshipType: int):
        match relationshipType:
            case 16:
                return RelationshipType.ONE_MANY()
            case 8:
                return RelationshipType.ONE_ONLY()
            case 4:
                return RelationshipType.ZERO_MANY()
            case 2:
                return RelationshipType.ZERO_ONLY()


class IOUtils:
    @staticmethod
    def load(path: str) -> models.ErdEditorSchema:
        with open(path, "rb") as file:
            return models.ErdEditorSchema.model_validate_json(file.read())

    @staticmethod
    def dump(path: str, document: minidom.Document) -> None:
        with open(path, "wb") as file:
            file.write(document.toprettyxml(encoding="utf-8"))


def key_cell_value_builder(
    keys: int,
    foreignKeyCounter: int = 0,
) -> str:
    result = []
    if keys & 1:
        result.append("PK")
    if keys & 2:
        result.append(f"FK{foreignKeyCounter}")
    return ",".join(result)


def create_element(
    document: minidom.Document,
    tagName: str,
    *children: minidom.Element,
    **attributes,
) -> minidom.Element:
    element = document.createElement(tagName)
    for attname, value in attributes.items():
        element.setAttribute(attname.strip("_"), str(value))
    for child in children:
        element.appendChild(child)
    return element


def create_rectangle(
    document: minidom.Document,
    width: int,
    height: int,
) -> minidom.Element:
    return create_element(
        document,
        Tags.MX_RECTANGLE,
        width=width,
        height=height,
        _as="alternateBounds",
    )


def create_geometry(
    document: minidom.Document,
    width: int,
    height: int,
    x: int = 0,
    y: int = 0,
    rectangle: bool = False,
) -> minidom.Element:
    geometry = create_element(
        document,
        Tags.MX_GEOMETRY,
        width=width,
        height=height,
        x=x,
        y=y,
        _as="geometry",
    )
    if rectangle:
        geometry.appendChild(
            create_rectangle(
                document,
                width,
                height,
            )
        )
    return geometry


def create_table_cell(
    document: minidom.Document,
    tableEntity: models.TableEntities1,
) -> minidom.Element:
    return create_element(
        document,
        Tags.MX_CELL,
        create_geometry(
            document,
            Defaults.KEY_WIDTH + Defaults.COLUMN_NAME_WIDTH,
            Defaults.HEIGHT * (len(tableEntity.columnIds) + 1),
            abs(tableEntity.ui.x),
            abs(tableEntity.ui.y),
        ),
        _id=tableEntity.id,
        value=tableEntity.name,
        style=Styles.TABLE.format(START_SIZE=Defaults.HEIGHT),
        vertex=1,
        parent="root",
    )


def create_column_base_cell(
    document: minidom.Document,
    columnEntity: models.TableColumnEntities1,
    y: int,
    top: bool = False,
) -> minidom.Element:
    return create_element(
        document,
        Tags.MX_CELL,
        create_geometry(
            document,
            Defaults.KEY_WIDTH + Defaults.COLUMN_NAME_WIDTH,
            Defaults.HEIGHT,
            y=y,
        ),
        _id=f"{columnEntity.id}-base",
        value="",
        style=Styles.COLUMN_BASE.format(
            START_SIZE=0,
            TOP=1 if top else 0,
        ),
        vertex=1,
        parent=columnEntity.tableId,
    )


def create_column_key_cell(
    document: minidom.Document,
    columnEntity: models.TableColumnEntities1,
    foreignKeyCounter: int = 0,
    isDoubleKey: bool = False,
) -> minidom.Element:
    return create_element(
        document,
        Tags.MX_CELL,
        create_geometry(
            document,
            Defaults.KEY_WIDTH * (2 if isDoubleKey else 1),
            Defaults.HEIGHT,
            rectangle=True,
        ),
        _id=f"{columnEntity.id}-key",
        value=key_cell_value_builder(
            columnEntity.ui.keys,
            foreignKeyCounter,
        ),
        style=Styles.COLUMN_KEY,
        vertex=1,
        parent=f"{columnEntity.id}-base",
    )


def create_column_name_cell(
    document: minidom.Document,
    columnEntity: models.TableColumnEntities1,
    isDoubleKey: bool = False,
) -> minidom.Element:
    return create_element(
        document,
        Tags.MX_CELL,
        create_geometry(
            document,
            Defaults.COLUMN_NAME_WIDTH,
            Defaults.HEIGHT,
            Defaults.KEY_WIDTH * (2 if isDoubleKey else 1),
            rectangle=True,
        ),
        _id=f"{columnEntity.id}-name",
        value=columnEntity.name,
        style=Styles.COLUMN_NAME.format(
            FONT_STYLE=5 if columnEntity.ui.keys & 1 else 0,
        ),
        vertex=1,
        parent=f"{columnEntity.id}-base",
    )


def create_relation_edge_cell(
    document: minidom.Document,
    relationshipEntity: models.RelationshipEntities1,
):
    relationshipType = RelationshipType.get(relationshipEntity.relationshipType)
    startPoint = relationshipEntity.start
    endPoint = relationshipEntity.end
    startToEnd = startPoint.x < endPoint.x
    return create_element(
        document,
        Tags.MX_CELL,
        create_geometry(document, 100, 100),
        _id=relationshipEntity.id,
        value="",
        style=Styles.RELATION_EDGE.format(
            START_ARROW=relationshipType.startArrow,
            END_ARROW=relationshipType.endArrow,
            FROM=1 if startToEnd else 0,
            TO=0 if startToEnd else 1,
        ),
        edge=1,
        parent="root",
        source=f"{startPoint.columnIds[0]}-base",
        target=f"{endPoint.columnIds[0]}-base",
    )


def create_root(
    document: minidom.Document,
    schema: models.ErdEditorSchema,
) -> minidom.Element:
    root = create_element(
        document,
        Tags.ROOT,
        create_element(document, Tags.MX_CELL, _id=0),
        create_element(document, Tags.MX_CELL, _id="root", parent=0),
    )
    for tableId in schema.doc.tableIds:
        tableEntity = schema.collections.tableEntities.root[tableId]
        root.appendChild(create_table_cell(document, tableEntity))

        columnEntities = [
            schema.collections.tableColumnEntities.root[columnId]
            for columnId in tableEntity.columnIds
        ]

        y = Defaults.HEIGHT
        foreignKeyCounter = 1
        isPrimaryKey = True
        isDoubleKey = any(map(lambda x: x.ui.keys == 3, columnEntities))

        for key in (1, 3, 2, 0):
            for columnEntity in filter(lambda x: x.ui.keys == key, columnEntities):
                root.appendChild(
                    create_column_base_cell(
                        document,
                        columnEntity,
                        y,
                        top=isPrimaryKey and not key & 1,
                    )
                )
                root.appendChild(
                    create_column_key_cell(
                        document,
                        columnEntity,
                        foreignKeyCounter,
                        isDoubleKey,
                    )
                )
                root.appendChild(
                    create_column_name_cell(
                        document,
                        columnEntity,
                        isDoubleKey,
                    )
                )

                if key > 1:
                    foreignKeyCounter += 1
                y += Defaults.HEIGHT
                if isPrimaryKey and not key & 1:
                    isPrimaryKey = False

    for relationshipId in schema.doc.relationshipIds:
        root.appendChild(
            create_relation_edge_cell(
                document,
                schema.collections.relationshipEntities.root[relationshipId],
            )
        )

    return root


def create_graph_model(
    document: minidom.Document,
    schema: models.ErdEditorSchema,
) -> minidom.Element:
    return create_element(
        document,
        Tags.MX_GRAPH_MODEL,
        create_root(document, schema),
        pageWidth=schema.settings.width,
        pageHeight=schema.settings.height,
        dx=abs(schema.settings.scrollLeft),
        dy=abs(schema.settings.scrollTop),
        grid=0,
        gridSize=10,
        tooltips=1,
        connect=1,
        arrows=1,
        fold=1,
        page=1,
        pageScale=1,
    )


def create_diagram(
    document: minidom.Document,
    schema: models.ErdEditorSchema,
) -> minidom.Element:
    return create_element(
        document,
        Tags.DIAGRAM,
        create_graph_model(document, schema),
        name=schema.settings.databaseName,
        _id="DATABASE_DIAGRAM",
    )


def create_file(
    document: minidom.Document,
    schema: models.ErdEditorSchema,
) -> minidom.Document:
    return create_element(
        document,
        Tags.MX_FILE,
        create_diagram(document, schema),
    )


__all__ = (
    Defaults,
    Styles,
    Tags,
    IOUtils,
    key_cell_value_builder,
    create_column_base_cell,
    create_column_key_cell,
    create_column_name_cell,
    create_diagram,
    create_element,
    create_geometry,
    create_file,
    create_graph_model,
    create_rectangle,
    create_relation_edge_cell,
    create_root,
    create_table_cell,
)
