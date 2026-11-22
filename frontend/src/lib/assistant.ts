// Client for the Admission Assistant API (backend/api/assistant.py).
// The assistant's answers are produced server-side from Decision-Intel data;
// nothing here generates or alters a prediction.
import { api } from './api';

export type AssistantLink = { label: string; href: string };

export type AssistantFactor = {
    text: string;
    impact: number;
    direction: 'up' | 'down';
    strength: string;
};

export type AssistantLeadCard = {
    lead_id: string;
    display_id: string;
    name: string | null;
    probability: number;
    band: 'High' | 'Medium' | 'Low' | string;
    segment: string | null;
    source: 'stored' | 'live' | string;
    model: string;
    positive: AssistantFactor[];
    negative: AssistantFactor[];
};

export type AssistantMessage = {
    id: string;
    role: 'user' | 'assistant';
    text: string;
    created_at: number;
    kind?: string;
    suggestions?: string[];
    links?: AssistantLink[];
    card?: AssistantLeadCard | null;
    notice?: string | null;
    sources?: string[];
    engine?: 'grounded' | 'llm' | string;
    confidence?: number;
    context?: { path?: string | null; lead_id?: string | null };
};

export type AssistantWelcome = {
    text: string;
    suggestions: string[];
    role: string;
    llm_enabled: boolean;
};

export type AssistantContext = { path?: string; lead_id?: string };

const LEAD_PAGE = /^\/student-leads\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?$/i;

/** The lead the user is looking at, when the current page is a lead detail page. */
export function leadFromPath(pathname: string): string | undefined {
    return LEAD_PAGE.exec(pathname)?.[1];
}

export function loadWelcome(leadId?: string): Promise<AssistantWelcome> {
    const query = leadId ? `?lead_id=${encodeURIComponent(leadId)}` : '';
    return api(`/assistant/welcome${query}`);
}

export function loadHistory(limit = 50): Promise<AssistantMessage[]> {
    return api(`/assistant/history?limit=${limit}`);
}

export function clearHistory(): Promise<{ deleted: number }> {
    return api('/assistant/history', { method: 'DELETE' });
}

export function sendMessage(message: string, context: AssistantContext): Promise<AssistantMessage> {
    return api('/assistant/chat', { method: 'POST', body: JSON.stringify({ message, context }) });
}

/** Split assistant text into paragraphs and bullet lists for safe rendering (no HTML). */
export type TextBlock = { type: 'p'; text: string } | { type: 'list'; items: string[] };

export function toBlocks(text: string): TextBlock[] {
    const blocks: TextBlock[] = [];
    for (const chunk of text.split(/\n{2,}/)) {
        const lines = chunk.split('\n').map(line => line.trimEnd()).filter(Boolean);
        let paragraph: string[] = [];
        let items: string[] = [];
        const flushParagraph = () => { if (paragraph.length) { blocks.push({ type: 'p', text: paragraph.join(' ') }); paragraph = []; } };
        const flushList = () => { if (items.length) { blocks.push({ type: 'list', items }); items = []; } };
        for (const line of lines) {
            const bullet = /^\s*[-•]\s+(.*)$/.exec(line);
            if (bullet) { flushParagraph(); items.push(bullet[1]); }
            else { flushList(); paragraph.push(line.trim()); }
        }
        flushParagraph();
        flushList();
    }
    return blocks;
}
