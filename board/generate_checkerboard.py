"""Generate the A4 landscape, 10 x 7 printable calibration board."""

from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


COLS = 10
ROWS = 7
SQUARE_MM = 25
OUTPUT = Path(__file__).with_name("checkerboard_9x6_25mm_A4.pdf")


def main() -> None:
    page_width, page_height = landscape(A4)
    square = SQUARE_MM * mm
    board_width = COLS * square
    board_height = ROWS * square
    left = (page_width - board_width) / 2
    bottom = (page_height - board_height) / 2

    pdf = canvas.Canvas(str(OUTPUT), pagesize=(page_width, page_height), pageCompression=0)
    pdf.setTitle("Camera calibration checkerboard - 9x6 inner corners, 25 mm")
    pdf.setAuthor("CameraCalibration project")
    pdf.setFillColorRGB(0, 0, 0)

    for row in range(ROWS):
        for col in range(COLS):
            if (row + col) % 2 == 0:
                pdf.rect(left + col * square, bottom + row * square, square, square, fill=1, stroke=0)

    pdf.showPage()
    pdf.save()
    print(OUTPUT)


if __name__ == "__main__":
    main()
