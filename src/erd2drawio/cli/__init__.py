import argparse
from xml.dom.minidom import Document

from erd2drawio import IOUtils, create_file


def main():
    parser = argparse.ArgumentParser(
        description="ERD Editor .erd file to .drawio convertor"
    )
    parser.add_argument(
        "-i",
        "--input",
        help="path to input file (*.erd)",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="path to output file (*.drawio)",
        required=True,
    )
    args = parser.parse_args()

    schema = IOUtils.load(args.input)
    document = Document()
    document.appendChild(create_file(document, schema))
    IOUtils.dump(args.output, document)
