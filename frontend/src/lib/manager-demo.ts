export type LeadStatus = 'New' | 'Contacted' | 'Counselling' | 'Application' | 'Admitted' | 'Not Converted';
export type PredictionType = 'High' | 'Medium' | 'Low';

export type ManagerLead = {
  id: string;
  student_name: string;
  email: string;
  phone: string;
  location: string;
  qualification: string;
  academic_score: number;
  graduation_year: number;
  academic_background: string;
  course_interested: string;
  preferred_program: string;
  preferred_intake: string;
  lead_source: string;
  remarks: string;
  lead_status: LeadStatus;
  prediction: PredictionType;
  probability: number;
  assigned_to: string;
  enquiry_date: string;
  source: string;
  stage_index: number;
};

export const managerLeads: ManagerLead[] = [
  {
    id: 'lead-1001',
    student_name: 'Arun Kumar',
    email: 'arun.kumar@example.com',
    phone: '+91 9876543210',
    location: 'Bengaluru',
    qualification: 'B.Sc. Computer Science',
    academic_score: 88,
    graduation_year: 2025,
    academic_background: 'Computer Science / Mathematics',
    course_interested: 'MCA',
    preferred_program: 'Master of Computer Applications',
    preferred_intake: 'July 2026',
    lead_source: 'Google Ads',
    remarks: 'Interested in AI and software engineering pathways.',
    lead_status: 'Counselling',
    prediction: 'High',
    probability: 86,
    assigned_to: 'Priya Nair',
    enquiry_date: '2026-08-12',
    source: 'Google Ads',
    stage_index: 2
  },
  {
    id: 'lead-1002',
    student_name: 'Neha Sharma',
    email: 'neha.sharma@example.com',
    phone: '+91 9123456781',
    location: 'Delhi',
    qualification: 'BBA',
    academic_score: 81,
    graduation_year: 2024,
    academic_background: 'Business Administration',
    course_interested: 'MBA',
    preferred_program: 'MBA in Marketing',
    preferred_intake: 'August 2026',
    lead_source: 'Website',
    remarks: 'Strong interest in digital marketing and brand strategy.',
    lead_status: 'Application',
    prediction: 'Medium',
    probability: 72,
    assigned_to: 'Rahul Verma',
    enquiry_date: '2026-08-19',
    source: 'Website',
    stage_index: 3
  },
  {
    id: 'lead-1003',
    student_name: 'Priyanka Rao',
    email: 'priyanka.rao@example.com',
    phone: '+91 9988776655',
    location: 'Hyderabad',
    qualification: 'B.E. Electronics',
    academic_score: 91,
    graduation_year: 2025,
    academic_background: 'Electronics and Communications',
    course_interested: 'B.Tech',
    preferred_program: 'B.Tech in Artificial Intelligence',
    preferred_intake: 'September 2026',
    lead_source: 'Referral',
    remarks: 'Referred by alumni network and looking for strong placement support.',
    lead_status: 'Application',
    prediction: 'High',
    probability: 91,
    assigned_to: 'Aisha Khan',
    enquiry_date: '2026-08-07',
    source: 'Referral',
    stage_index: 3
  },
  {
    id: 'lead-1004',
    student_name: 'Ritesh Kulkarni',
    email: 'ritesh.kulkarni@example.com',
    phone: '+91 9090909090',
    location: 'Pune',
    qualification: 'B.Com',
    academic_score: 68,
    graduation_year: 2024,
    academic_background: 'Commerce and Finance',
    course_interested: 'BBA',
    preferred_program: 'BBA in Finance',
    preferred_intake: 'July 2026',
    lead_source: 'Instagram',
    remarks: 'Interested in scholarships and finance-focused learning outcomes.',
    lead_status: 'Contacted',
    prediction: 'Medium',
    probability: 64,
    assigned_to: 'Nisha Thomas',
    enquiry_date: '2026-08-22',
    source: 'Instagram',
    stage_index: 1
  },
  {
    id: 'lead-1005',
    student_name: 'Meera Nair',
    email: 'meera.nair@example.com',
    phone: '+91 9812345600',
    location: 'Kochi',
    qualification: 'B.Sc. Mathematics',
    academic_score: 59,
    graduation_year: 2023,
    academic_background: 'Mathematics and Statistics',
    course_interested: 'M.Sc. Analytics',
    preferred_program: 'M.Sc. in Data Analytics',
    preferred_intake: 'January 2027',
    lead_source: 'Phone',
    remarks: 'Shows interest but requested more information on return on investment.',
    lead_status: 'New',
    prediction: 'Low',
    probability: 42,
    assigned_to: 'Surya Rao',
    enquiry_date: '2026-08-28',
    source: 'Phone',
    stage_index: 0
  },
  {
    id: 'lead-1006',
    student_name: 'Vikram Singh',
    email: 'vikram.singh@example.com',
    phone: '+91 9765432109',
    location: 'Jaipur',
    qualification: 'B.E. Civil',
    academic_score: 84,
    graduation_year: 2025,
    academic_background: 'Civil Engineering',
    course_interested: 'M.Tech',
    preferred_program: 'M.Tech in Infrastructure Management',
    preferred_intake: 'August 2026',
    lead_source: 'Education Portals',
    remarks: 'Career growth and infrastructure management were primary decision drivers.',
    lead_status: 'Admitted',
    prediction: 'High',
    probability: 88,
    assigned_to: 'Dhruv Mehta',
    enquiry_date: '2026-08-02',
    source: 'Education Portals',
    stage_index: 4
  }
];

export const managerFunnelStages = [
  { name: 'Enquiry', count: 1248, conversion: 100, dropOff: 0 },
  { name: 'Contacted', count: 978, conversion: 78.3, dropOff: 21.7 },
  { name: 'Counselling', count: 746, conversion: 59.8, dropOff: 23.7 },
  { name: 'Application', count: 440, conversion: 35.3, dropOff: 41.0 },
  { name: 'Admission', count: 192, conversion: 15.4, dropOff: 56.4 }
];

export const managerChannels = [
  { channel: 'Google Ads', spend: 220000, leads: 310, applications: 146, admissions: 58, conversion: 18.7, costPerLead: 710, costPerAdmission: 3793 },
  { channel: 'Instagram', spend: 160000, leads: 256, applications: 118, admissions: 41, conversion: 16.0, costPerLead: 625, costPerAdmission: 3902 },
  { channel: 'Facebook', spend: 110000, leads: 191, applications: 69, admissions: 22, conversion: 11.5, costPerLead: 576, costPerAdmission: 5000 },
  { channel: 'Website', spend: 85000, leads: 172, applications: 94, admissions: 44, conversion: 25.6, costPerLead: 494, costPerAdmission: 1932 },
  { channel: 'Education Portals', spend: 210000, leads: 244, applications: 112, admissions: 38, conversion: 15.6, costPerLead: 860, costPerAdmission: 5526 },
  { channel: 'Email', spend: 65000, leads: 144, applications: 79, admissions: 29, conversion: 20.1, costPerLead: 451, costPerAdmission: 2241 },
  { channel: 'Referral', spend: 45000, leads: 128, applications: 88, admissions: 36, conversion: 28.1, costPerLead: 352, costPerAdmission: 1250 }
];

export const managerCampaigns = [
  { name: 'MCA Admission Campaign', channel: 'Google Ads', budget: 210000, spend: 195000, leads: 440, applications: 198, admissions: 82, conversion: 18.6 },
  { name: 'MBA Admission Campaign', channel: 'Website', budget: 180000, spend: 168000, leads: 360, applications: 146, admissions: 54, conversion: 15.0 },
  { name: 'Engineering Campaign', channel: 'Education Portals', budget: 220000, spend: 200000, leads: 382, applications: 118, admissions: 40, conversion: 10.5 },
  { name: 'Scholarship Campaign', channel: 'Instagram', budget: 90000, spend: 86000, leads: 214, applications: 89, admissions: 31, conversion: 14.5 },
  { name: 'Early Admission Campaign', channel: 'Email', budget: 70000, spend: 64000, leads: 182, applications: 92, admissions: 33, conversion: 18.1 }
];

export const dashboardStats = [
  { label: 'Student Enquiries', value: '1,248', delta: '+12.4%' },
  { label: 'Admission Leads', value: '864', delta: '+8.7%' },
  { label: 'High-Potential Leads', value: '286', delta: '+14.2%' },
  { label: 'Predicted Admissions', value: '192', delta: '+9.5%' },
  { label: 'Conversion Rate', value: '22.2%', delta: '+3.4%' },
  { label: 'Marketing Spend', value: '₹4.8L', delta: '₹1.2L used' }
];

export const managerSegments = [
  { title: 'High-Intent Students', count: 286, avgProbability: 88, conversionRate: 31.4, characteristics: 'Strong academic fit, quick response, high application intent.' },
  { title: 'Moderate-Intent Students', count: 412, avgProbability: 68, conversionRate: 21.0, characteristics: 'Prospective students with good fit but slower engagement.' },
  { title: 'Low-Intent Students', count: 198, avgProbability: 41, conversionRate: 8.1, characteristics: 'Need more nurturing and program education support.' }
];

export const managerRecommendations = [
  {
    title: 'MCA leads show higher conversion intent',
    recommendation: 'Evaluate campaign allocation toward high-performing MCA-focused channels and retargeting audiences.',
    reason: 'Strong conversion and lead quality remain concentrated in MCA and engineering interest segments.',
    metric: 'Conversion Rate: 28%',
    period: 'Current selected period',
    type: 'Insight',
    demo: true
  },
  {
    title: 'Website and referral sources show stronger admissions',
    recommendation: 'Increase budget share for referral and website channels with a measured retargeting strategy.',
    reason: 'These sources deliver lower cost per admission while maintaining stronger conversion outcomes.',
    metric: 'Admissions per 100 leads: 26',
    period: 'Last 30 days',
    type: 'Insight',
    demo: true
  },
  {
    title: 'Counselling follow-up should be prioritized for medium-probability leads',
    recommendation: 'Increase counselling touchpoints for medium-intent applicants with incomplete application progress.',
    reason: 'Early follow-up improves completion probability and reduces drop-off before the admissions stage.',
    metric: 'Drop-off after counselling: 41%',
    period: 'Last 2 weeks',
    type: 'Action',
    demo: true
  }
];

export const managerReports = [
  { label: 'Lead Report', description: 'Monitor active leads, status changes, and conversion movement.', lastUpdated: 'Today, 09:40 AM', type: 'lead' },
  { label: 'Prediction Report', description: 'Track probability scores and forecasted admissions across student segments.', lastUpdated: 'Today, 08:12 AM', type: 'prediction' },
  { label: 'Funnel Report', description: 'Review funnel conversion and stage retention trends across admissions.', lastUpdated: 'Yesterday', type: 'funnel' },
  { label: 'Channel Report', description: 'Break down lead and admission performance by acquisition channel.', lastUpdated: 'Yesterday', type: 'channel' },
  { label: 'Campaign Report', description: 'Compare spend, leads, and conversions across campaigns.', lastUpdated: '2 days ago', type: 'campaign' },
  { label: 'Budget Report', description: 'Review allocation, utilization, and optimization scenarios.', lastUpdated: '3 days ago', type: 'budget' }
];

export const managerNotifications = [
  { id: 'n1', title: 'New Student Lead', description: 'Arun Kumar has entered a high-intent stage in MCA counselling.', time: '2 mins ago', read: false, type: 'lead' },
  { id: 'n2', title: 'New Application', description: 'Priyanka Rao submitted her AI engineering application package.', time: '18 mins ago', read: false, type: 'application' },
  { id: 'n3', title: 'Counselling Reminder', description: 'Three medium-probability leads are due for follow-up today.', time: '1 hour ago', read: true, type: 'reminder' },
  { id: 'n4', title: 'Prediction Completed', description: 'Prediction summary updated for the latest enrolment cohort.', time: '3 hours ago', read: true, type: 'prediction' },
  { id: 'n5', title: 'Budget Insight', description: 'Referral and website channels show a stronger conversion profile this week.', time: '1 day ago', read: true, type: 'budget' }
];

export const managerProfile = {
  name: 'Adminstrator',
  email: 'priya.nair@decisionintel.edu',
  phone: '+91 98765 43210',
  institution: 'DecisionIntel Academy',
  role: 'Admission Manager'
};

export const managerSettings = {
  emailNotifications: true,
  leadNotifications: true,
  predictionNotifications: true,
  marketingInsightNotifications: true
};

export const managerBudget = {
  totalBudget: 1000000,
  spent: 720000,
  remaining: 280000,
  allocations: [
    { channel: 'Google Ads', currentAmount: 240000, percent: 24 },
    { channel: 'Instagram', currentAmount: 180000, percent: 18 },
    { channel: 'Facebook', currentAmount: 120000, percent: 12 },
    { channel: 'Education Portals', currentAmount: 200000, percent: 20 },
    { channel: 'Email', currentAmount: 130000, percent: 13 },
    { channel: 'Referral', currentAmount: 130000, percent: 13 }
  ]
};

export const whatIfScenario = {
  current: { leads: 1248, applications: 440, admissions: 192, conversionRate: 15.4, costPerAdmission: 3749 },
  simulated: { leads: 1376, applications: 494, admissions: 224, conversionRate: 16.3, costPerAdmission: 3521 }
};

export const shapDemo = {
  positive: [
    { name: 'Academic Score', value: 0.28 },
    { name: 'Course Interest', value: 0.21 },
    { name: 'Counselling Status', value: 0.17 },
    { name: 'Lead Source', value: 0.12 }
  ],
  negative: [
    { name: 'Application Delay', value: -0.18 },
    { name: 'Low Engagement', value: -0.11 }
  ],
  summary: 'Demo Explanation: This lead is likely to convert because of strong academic performance and consistent counselling engagement. Delayed application steps and lower engagement slightly reduce conversion likelihood.'
};

export function getLeadById(id: string) {
  return managerLeads.find((lead) => lead.id === id) ?? null;
}

export function getLeadStatusCounts() {
  return {
    total: managerLeads.length,
    new: managerLeads.filter((lead) => lead.lead_status === 'New').length,
    highPotential: managerLeads.filter((lead) => lead.prediction === 'High').length,
    inCounselling: managerLeads.filter((lead) => lead.lead_status === 'Counselling').length,
    applications: managerLeads.filter((lead) => lead.lead_status === 'Application').length,
    admitted: managerLeads.filter((lead) => lead.lead_status === 'Admitted').length
  };
}
