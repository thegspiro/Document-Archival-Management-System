"""EAD3 XML export for collection-level subtrees."""

from lxml import etree

from app.models.arrangement import ArrangementNode

EAD3_NS = "http://ead3.archivists.org/schema/"
NSMAP = {None: EAD3_NS}


def node_to_ead3(
    node: ArrangementNode,
    children: list[ArrangementNode],
    institution_name: str = "",
) -> bytes:
    """Generate EAD3 XML for an arrangement node and its children."""
    root = etree.Element(f"{{{EAD3_NS}}}ead", nsmap=NSMAP)

    # Control section
    control = etree.SubElement(root, f"{{{EAD3_NS}}}control")
    recordid = etree.SubElement(control, f"{{{EAD3_NS}}}recordid")
    recordid.text = node.identifier or str(node.id)

    filedesc = etree.SubElement(control, f"{{{EAD3_NS}}}filedesc")
    titlestmt = etree.SubElement(filedesc, f"{{{EAD3_NS}}}titlestmt")
    titleproper = etree.SubElement(titlestmt, f"{{{EAD3_NS}}}titleproper")
    titleproper.text = node.title

    if institution_name:
        maintenanceagency = etree.SubElement(control, f"{{{EAD3_NS}}}maintenanceagency")
        agencyname = etree.SubElement(maintenanceagency, f"{{{EAD3_NS}}}agencyname")
        agencyname.text = institution_name

    # Archival description
    archdesc = etree.SubElement(root, f"{{{EAD3_NS}}}archdesc")
    archdesc.set("level", node.level_type)

    did = etree.SubElement(archdesc, f"{{{EAD3_NS}}}did")
    unittitle = etree.SubElement(did, f"{{{EAD3_NS}}}unittitle")
    unittitle.text = node.title

    if node.identifier:
        unitid = etree.SubElement(did, f"{{{EAD3_NS}}}unitid")
        unitid.text = node.identifier

    if node.date_start or node.date_end:
        unitdate = etree.SubElement(did, f"{{{EAD3_NS}}}unitdate")
        if node.date_start and node.date_end:
            unitdate.text = f"{node.date_start}/{node.date_end}"
        elif node.date_start:
            unitdate.text = str(node.date_start)

    if node.description:
        scopecontent = etree.SubElement(archdesc, f"{{{EAD3_NS}}}scopecontent")
        p = etree.SubElement(scopecontent, f"{{{EAD3_NS}}}p")
        p.text = node.description

    # Child components
    if children:
        dsc = etree.SubElement(archdesc, f"{{{EAD3_NS}}}dsc")
        for child in children:
            _add_component(dsc, child)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


def _add_component(parent: etree._Element, node: ArrangementNode) -> None:
    """Recursively add a component to the EAD3 tree."""
    c = etree.SubElement(parent, f"{{{EAD3_NS}}}c")
    c.set("level", node.level_type)

    did = etree.SubElement(c, f"{{{EAD3_NS}}}did")
    unittitle = etree.SubElement(did, f"{{{EAD3_NS}}}unittitle")
    unittitle.text = node.title

    if node.identifier:
        unitid = etree.SubElement(did, f"{{{EAD3_NS}}}unitid")
        unitid.text = node.identifier

    if node.description:
        scopecontent = etree.SubElement(c, f"{{{EAD3_NS}}}scopecontent")
        p = etree.SubElement(scopecontent, f"{{{EAD3_NS}}}p")
        p.text = node.description
