/** The first request sees the Coco role; only Pi's guide_request narrows later context. */
import type { AgentTool } from '@earendil-works/pi-agent-core';

export type GuideRequestKind = 'question' | 'progress' | 'continue' | 'new_goal' | 'amend' | 'stop' | 'abandon';
export interface TurnContext {
  role: 'keke';
  [key: string]: unknown;
}
export interface PromptModules {
  expression: string;
  sections: Array<{name:string; text:string}>;
}
const shoppingSections = new Set(['dishes', 'purchase', 'exploration', 'selection', 'pending']);
const shoppingTools = new Set(['propose_dish', 'propose_purchase', 'explore_products', 'select_question_products']);
const sharedContext = new Set(['role', 'has_active_task', 'general_history', 'memory', 'memory_list_refs', 'comparison_candidates']);
const includeShopping = (kind: GuideRequestKind | undefined) => kind === undefined || ['continue', 'new_goal', 'amend'].includes(kind);

export function selectTools(tools: AgentTool[], kind?: GuideRequestKind): AgentTool[] {
  return includeShopping(kind) ? tools : tools.filter(tool => !shoppingTools.has(tool.name));
}

export function composePrompt(modules: PromptModules, context: TurnContext, kind?: GuideRequestKind): string {
  const relevant = includeShopping(kind);
  const sections = modules.sections.filter(section => relevant || !shoppingSections.has(section.name));
  const facts = relevant ? context : Object.fromEntries(Object.entries(context).filter(([key]) => sharedContext.has(key)));
  return modules.expression + sections.map(section => section.text).join('') + JSON.stringify(facts);
}
