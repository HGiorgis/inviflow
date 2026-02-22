from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import os

def generate_invoice_pdf(deposit):
    """Generate PDF invoice for a deposit"""
    buffer = BytesIO()
    
    # Create the PDF object
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='RightAlign',
        parent=styles['Normal'],
        alignment=2  # Right align
    ))
    
    # Company header
    elements.append(Paragraph("InviFlow", styles['Title']))
    elements.append(Paragraph("Investment Portfolio Platform", styles['Normal']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Invoice title
    elements.append(Paragraph(f"INVOICE", styles['Heading1']))
    elements.append(Spacer(1, 0.15*inch))
    
    # Invoice details
    invoice_data = [
        ["Invoice Number:", deposit.invoice_number],
        ["Date:", deposit.created_at.strftime('%Y-%m-%d')],
        ["Status:", deposit.status.upper()],
        ["Payment Method:", deposit.payment_method.replace('_', ' ').title()],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[100, 300])
    invoice_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Client information
    elements.append(Paragraph("Bill To:", styles['Heading2']))
    client_data = [
        ["Name:", deposit.user.get_full_name() or deposit.user.username],
        ["Email:", deposit.user.email],
    ]
    
    if hasattr(deposit.user, 'profile') and deposit.user.profile.company:
        client_data.append(["Company:", deposit.user.profile.company])
    
    client_table = Table(client_data, colWidths=[80, 320])
    client_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Items table
    items_data = [
        ['Description', 'Quantity', 'Unit Price', 'Total'],
        [
            f"Deposit to Portfolio{f' - {deposit.stock.symbol}' if deposit.stock else ''}",
            '1',
            f"${deposit.amount}",
            f"${deposit.amount}"
        ]
    ]
    
    items_table = Table(items_data, colWidths=[250, 80, 80, 80])
    items_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.15*inch))
    
    # Totals
    total_data = [
        ['Subtotal:', f"${deposit.amount}"],
        ['Tax (0%):', '$0.00'],
        ['Total:', f"${deposit.amount}"],
    ]
    
    total_table = Table(total_data, colWidths=[400, 100])
    total_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, -1), (-1, -1), 12),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Footer
    elements.append(Paragraph("Thank you for your business!", styles['Italic']))
    elements.append(Paragraph("InviFlow - Investment Portfolio Platform", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def generate_simple_invoice(deposit):
    """Simpler invoice generator using canvas directly"""
    buffer = BytesIO()
    
    # Create canvas
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "INVIFLOW")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, "Investment Portfolio Platform")
    
    # Invoice title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 120, "INVOICE")
    
    # Invoice details
    c.setFont("Helvetica", 10)
    y = height - 150
    
    details = [
        f"Invoice Number: {deposit.invoice_number}",
        f"Date: {deposit.created_at.strftime('%Y-%m-%d')}",
        f"Status: {deposit.status.upper()}",
        f"Payment Method: {deposit.payment_method.replace('_', ' ').title()}",
    ]
    
    for detail in details:
        c.drawString(50, y, detail)
        y -= 20
    
    # Client info
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Bill To:")
    y -= 20
    
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Name: {deposit.user.get_full_name() or deposit.user.username}")
    y -= 15
    c.drawString(50, y, f"Email: {deposit.user.email}")
    
    if hasattr(deposit.user, 'profile') and deposit.user.profile.company:
        y -= 15
        c.drawString(50, y, f"Company: {deposit.user.profile.company}")
    
    # Table header
    y -= 40
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Description")
    c.drawString(300, y, "Amount")
    
    # Line
    y -= 10
    c.line(50, y, 500, y)
    
    # Item
    y -= 20
    c.setFont("Helvetica", 10)
    desc = f"Deposit to Portfolio{f' - {deposit.stock.symbol}' if deposit.stock else ''}"
    c.drawString(50, y, desc)
    c.drawString(300, y, f"${deposit.amount}")
    
    # Line
    y -= 10
    c.line(50, y, 500, y)
    
    # Total
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(250, y, "Total:")
    c.drawString(300, y, f"${deposit.amount}")
    
    # Footer
    c.setFont("Helvetica-Italic", 10)
    c.drawString(50, 50, "Thank you for your business!")
    c.drawString(50, 35, "InviFlow - Investment Portfolio Platform")
    
    # Save
    c.save()
    
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf