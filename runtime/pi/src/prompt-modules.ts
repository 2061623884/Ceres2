/** Relevance selection only. Pi still interprets the complete original request. */
import type { AgentTool } from '@earendil-works/pi-agent-core';

export interface TurnContext {
  capability: 'exploration' | 'purchase_modification' | 'factual_qa' | 'chat';
  [key: string]: unknown;
}
export interface PromptModules {
  expression: string;
  sections: Array<{name:string; text:string}>;
}
const shoppingSections = new Set(['dishes', 'purchase', 'exploration', 'selection', 'pending']);
const shoppingTools = new Set([ 'propose_dish', 'propose_purchase', 'explore_products', 'select_question_products']);
const sharedContext = new Set(['capability', 'has_active_task', 'general_history', 'memory', 'memory_list_refs']);
const shopping = (capability: TurnContext['capability']) => capability === 'exploration' || capability === 'purchase_modification';

export function selectTools(tools: AgentTool[], capability: TurnContext['capability']): AgentTool[] {
  if (shopping(capability)) return tools;
  return tools.filter(tool => !shoppingTools.has(tool.name) && (capability !== 'chat' || !['compare_products', 'search_dishes', 'search_recipe_relations'].includes(tool.name)));
}

export function composePrompt(modules: PromptModules, context: TurnContext, capability: TurnContext['capability']): string {
  const relevant = shopping(capability);
  const sections = modules.sections.filter(section => relevant || (!shoppingSections.has(section.name) && (capability !== 'chat' || !['comparison', 'dish_facts'].includes(section.name))));
  const facts = relevant ? context : Object.fromEntries(Object.entries(context).filter(([key]) => sharedContext.has(key) || (capability === 'factual_qa' && key === 'comparison_candidates')));
  return modules.expression + sections.map(section => section.text).join('') + JSON.stringify(facts);
}
