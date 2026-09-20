import { managerLeads, managerProfile } from './manager-demo';
import { reportCatalog, type ManagerReport, type ReportRow } from './manager-reports';
import additionalPrograms from './additional-programs.json';

export const courses: ReportRow[] = [...new Set(managerLeads.map(lead => lead.preferred_program))].map(program => {
    const leads = managerLeads.filter(lead => lead.preferred_program === program);
    return { program, course: leads[0].course_interested, intakes: [...new Set(leads.map(lead => lead.preferred_intake))].join(', '), enquiries: leads.length, applications: leads.filter(lead => lead.lead_status === 'Application').length, admitted: leads.filter(lead => lead.lead_status === 'Admitted').length, high_potential: leads.filter(lead => lead.prediction === 'High').length, assigned_managers: [...new Set(leads.map(lead => lead.assigned_to))].join(', ') };
});
courses.push(...additionalPrograms.map(item => ({
    program: item.program, course: item.course, intakes: 'Not scheduled', enquiries: 0,
    applications: 0, admitted: 0, high_potential: 0, assigned_managers: 'Not assigned'
})));
export const institutions: ReportRow[] = [{ institution: managerProfile.institution, contact_name: managerProfile.name, contact_role: managerProfile.role, email: managerProfile.email, phone: managerProfile.phone }];
export const suppliedDatasets: ManagerReport[] = [
    ...reportCatalog,
    { type: 'courses', label: 'Courses / Programs', description: 'Expanded program catalog with admission counts from supplied student leads. New programs have no enquiries yet.', rows: courses },
    { type: 'institutions', label: 'Institutions', description: 'Institution and contact details from the supplied manager profile.', rows: institutions }
];
