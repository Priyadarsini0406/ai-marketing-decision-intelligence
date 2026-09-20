import { analyticsSections, type FullAnalytics } from './manager-reports';

export async function analyticsPdf(snapshot: FullAnalytics): Promise<ArrayBuffer> {
    const [{ jsPDF }, { autoTable }] = await Promise.all([import('jspdf'), import('jspdf-autotable')]);
    const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
    doc.setProperties({ title: 'Complete Admission & Marketing Analytics', subject: 'All manager analytics reports', author: 'DecisionIntel' });
    const sections = analyticsSections(snapshot);
    doc.setTextColor(45, 32, 66);
    doc.setFontSize(24);
    doc.text('Admission & Marketing Analytics', 16, 24);
    doc.setFontSize(12);
    doc.text('Complete analytics report | Currency: INR', 16, 35);
    doc.setFontSize(10);
    doc.text(`Generated: ${snapshot.generated_at}`, 16, 44);
    doc.text(`Source: ${snapshot.source}`, 16, 51);
    autoTable(doc, {
        startY: 62, margin: { left: 16, right: 16, bottom: 16 },
        head: [['Contents', 'Records']], body: sections.slice(1).map(section => [section.title, section.rows.length]),
        theme: 'striped', headStyles: { fillColor: [65, 45, 92] }, styles: { fontSize: 10, cellPadding: 2 }
    });
    for (const section of sections.slice(1)) {
        const columns = [...new Set(section.rows.flatMap(row => Object.keys(row)))];
        // Split wide tables into readable groups, repeating the record identifier.
        const groups = columns.length <= 7 ? [columns] : Array.from({ length: Math.ceil((columns.length - 1) / 6) }, (_, index) => [columns[0], ...columns.slice(1 + index * 6, 7 + index * 6)]);
        for (let index = 0; index < groups.length; index++) {
            const group = groups[index];
            doc.addPage();
            autoTable(doc, {
                startY: 29, margin: { top: 29, left: 16, right: 16, bottom: 17 },
                head: [group.map(column => column.replaceAll('_', ' '))],
                body: section.rows.map(row => group.map(column => row[column] == null ? '-' : String(row[column]))),
                theme: 'striped', headStyles: { fillColor: [65, 45, 92], textColor: 255 },
                styles: { fontSize: 9, cellPadding: 3, overflow: 'linebreak', valign: 'top' },
                rowPageBreak: 'avoid', showHead: 'everyPage',
                didDrawPage: () => {
                    doc.setTextColor(45, 32, 66); doc.setFontSize(17);
                    doc.text(section.title + (groups.length > 1 ? ` (${index + 1}/${groups.length})` : ''), 16, 18);
                }
            });
        }
    }
    const pageCount = doc.getNumberOfPages();
    for (let page = 1; page <= pageCount; page++) {
        doc.setPage(page); doc.setFontSize(8); doc.setTextColor(110);
        doc.text('DecisionIntel | Complete analytics | INR', 16, 201);
        doc.text(`Page ${page} of ${pageCount}`, 281, 201, { align: 'right' });
    }
    return doc.output('arraybuffer');
}
