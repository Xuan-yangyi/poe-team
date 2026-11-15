import api from './client'

export interface AgentSkill {
  name: string
  description: string
  trigger_keywords: string
  action_type: string
  skill_prompt: string
  data_config?: Record<string, any>
}

export function listAgents() {
  return api.get('/agents')
}

export function getAgent(id: string) {
  return api.get(`/agents/${id}`)
}

export function createAgent(data: {
  name: string
  display_name: string
  avatar_emoji: string
  role_description: string
  system_prompt: string
  provider?: string
  api_base?: string
  api_key?: string
  agent_model?: string
  skills: AgentSkill[]
}) {
  return api.post('/agents', data)
}

export function updateAgent(id: string, data: Record<string, any>) {
  return api.put(`/agents/${id}`, data)
}

export function deleteAgent(id: string) {
  return api.delete(`/agents/${id}`)
}

// Skills
export function listSkills(agentId: string) {
  return api.get(`/agents/${agentId}/skills`)
}

export function addSkill(agentId: string, data: AgentSkill) {
  return api.post(`/agents/${agentId}/skills`, data)
}

export function updateSkill(agentId: string, skillId: string, data: Record<string, any>) {
  return api.put(`/agents/${agentId}/skills/${skillId}`, data)
}

export function deleteSkill(agentId: string, skillId: string) {
  return api.delete(`/agents/${agentId}/skills/${skillId}`)
}

// Add agent to group conversation
export function addAgentToGroup(conversationId: string, agentUserId: string) {
  return api.post(`/conversations/${conversationId}/members`, { user_id: agentUserId })
}