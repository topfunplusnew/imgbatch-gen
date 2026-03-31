export interface TaskStageEvent {
  stage: string
  label: string
  message: string
  status: string
  progress: number
  attempt: number
  timestamp: string
}

export interface ImageTask {
  task_id: string
  status: 'pending' | 'processing' | 'running' | 'completed' | 'failed' | 'cancelled'
  params?: any
  result?: any
  images?: any[]
  error?: string
  progress?: number
  stage?: string
  stage_label?: string
  stage_message?: string
  attempt?: number
  updated_at?: string
  stage_history?: TaskStageEvent[]
  metadata?: Record<string, any>
}

export interface BatchStageOverviewItem {
  stage: string
  label: string
  count: number
}

export interface BatchStatusDetail {
  current_stage: string
  current_stage_label: string
  current_stage_message: string
  progress_percent: number
  pending_tasks: number
  running_tasks: number
  completed_tasks: number
  failed_tasks: number
  stage_overview: BatchStageOverviewItem[]
}

export interface BatchTaskStatus {
  batch_id: string
  status: 'pending' | 'processing' | 'running' | 'completed' | 'failed' | 'cancelled'
  tasks?: ImageTask[]
  total: number
  completed: number
  failed: number
  pending?: number
  running?: number
  progress?: number
  stage?: string
  stage_label?: string
  stage_message?: string
  status_detail?: BatchStatusDetail
  created_at?: string
  completed_at?: string
  updated_at?: string
}

export interface ChatMessage {
  role: string
  content: string
  images?: string[]
  metadata?: Record<string, any>
}

export interface ChatRequest {
  messages: ChatMessage[]
  session_id?: string
  enable_context?: boolean
  files?: string[]
  stream?: boolean
  model?: string
  model_type?: string
  image_params?: {
    width?: number
    height?: number
    style?: string
    quality?: string
    n?: number
    negative_prompt?: string
    seed?: number
  }
}

export interface ConversationHistorySummary {
  session_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  image_count: number
}

export interface ConversationHistoryMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  model?: string
  provider?: string
  created_at?: string
  images?: string[]
  files?: Array<{
    id?: number
    original_filename?: string
    file_url?: string
    file_size?: number
    file_type?: string
    category?: string
    created_at?: string
  }>
}

export interface ConversationHistoryDetail {
  session_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  image_count: number
  file_count: number
  messages: ConversationHistoryMessage[]
  files: Array<{
    id?: number
    original_filename?: string
    file_url?: string
    file_size?: number
    file_type?: string
    category?: string
    created_at?: string
  }>
}

export interface BillingInfo {
  status: 'frozen' | 'deducted' | 'refunded' | 'insufficient' | 'error'
  freeze_id?: string | null
  points_amount: number
  money_amount: number
  cost_type: string
  description: string
  balance_after?: {
    points: number
    gift_points: number
    balance: number
  }
}

export interface Intent {
  type: string
  confidence: number
  parameters: Record<string, any>
  reasoning: string
}

export interface ChatResponse {
  message: ChatMessage
  intent?: Intent
  task_id?: string
  batch_id?: string
  requires_action: boolean
  metadata?: Record<string, any> & { billing?: BillingInfo }
}

export interface GenerateRequest {
  prompt: string
  width?: number
  height?: number
  style?: string
  quality?: string
  n?: number
  provider?: string
  model_name?: string
  extra_params?: Record<string, any>
}

export interface ModelInfo {
  id: string
  name: string
  provider: string
  type: 'image' | 'llm' | 'embedding'
}

export interface BatchGenerateRequest {
  prompts?: string[]
  file?: File
  provider?: string
  default_params?: {
    width?: number
    height?: number
    style?: string
    quality?: string
  }
}

export interface User {
  id: string
  username: string
  phone?: string
  email?: string
  role?: string
  status: string
  created_at?: string
}

export interface AccountInfo {
  user_id: string
  balance: number
  balance_yuan: number
  points: number
  gift_points: number
  gift_points_expiry: string | null
  total_points: number
  subscription_plan?: string
  subscription_expires_at?: string
  total_generated: number
  total_spent: number
  total_points_earned: number
}

export interface Transaction {
  id: string
  transaction_type: string
  amount: number
  points_change: number
  balance_after: number
  points_after: number
  description: string
  status: string
  created_at: string
}

export interface ConsumptionRecord {
  id: string
  model_name: string
  provider: string
  cost_type: string
  points_used: number
  amount: number
  prompt?: string
  image_count: number
  image_urls?: string[]
  status: 'success' | 'failed'
  error_reason?: string
  created_at: string
}

export interface ModelPrice {
  model_name: string
  display_name: string
  points: number
  amount: number
  amount_yuan: number
  description: string
}

export interface RechargeOption {
  id: string
  name: string
  amount: number
  amount_yuan: number
  points: number
  bonus: number
  popular: boolean
}

export interface BillingConfig {
  billing: {
    mode: string
    currency: string
    currency_symbol: string
  }
  initial_quota: {
    free_generations: number
  }
  limits: {
    guest: {
      daily_limit: number
    }
    order_expire_minutes: number
  }
}

export interface SystemConfigItem {
  config_key: string
  config_value: string
  config_type: string
  category: string
  description?: string
  updated_at?: string
}

export interface Order {
  order_id: string
  order_type: string
  amount: number
  amount_yuan: number
  payment_method: string
  status: string
  subject: string
  created_at: string
  paid_at?: string
}

export interface WithdrawalRecord {
  id: string
  withdrawal_id: string
  amount: number
  amount_yuan: number
  withdrawal_method: string
  withdrawal_account: string
  withdrawal_name: string
  status: string
  user_note?: string
  review_note?: string
  created_at?: string
  reviewed_at?: string
  completed_at?: string
}

export interface AdminWithdrawalRecord extends WithdrawalRecord {
  user_id: string
  username: string
  phone: string
  admin_id?: string
  payment_proof?: string
}

export interface Case {
  id: string
  title: string
  description?: string
  category: string
  tags?: string[]
  thumbnail_url?: string
  image_url?: string
  prompt: string
  negative_prompt?: string
  parameters?: Record<string, any>
  provider?: string
  model?: string
  is_published: boolean
  sort_order: number
  view_count: number
  use_count: number
  created_by?: string
  created_at: string
  updated_at: string
}

export interface GenerationRecord {
  id: string
  user_request_id: string
  provider: string
  model: string
  prompt: string
  negative_prompt: string
  width: number
  height: number
  n: number
  style?: string
  quality?: string
  status: 'completed' | 'failed' | 'pending' | 'processing'
  image_urls: string[]
  image_paths: string[]
  processing_time?: number
  start_time?: string
  end_time?: string
  created_at: string
  extra_params?: Record<string, any>
}

export interface UnifiedGenerationRecord {
  id: string
  type: 'chat' | 'async'
  model: string
  prompt: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  image_urls: string[]
  timestamp: string
  created_at: string
  provider?: string
  platform?: string
  processing_time?: number
  error?: string
}

export interface AdminUserListItem {
  id: string
  phone: string
  username: string
  status: string
  role: string
  created_at: string
  last_login_at: string
  points: number
  balance: number
  gift_points: number
  total_generated: number
  total_spent: number
  invite_count: number
}

export interface AdminUserDetail {
  id: string
  phone: string
  username: string
  status: string
  role: string
  created_at: string
  last_login_at: string
  last_login_ip: string
  phone_verified: boolean
  points: number
  balance: number
  gift_points: number
  total_generated: number
  total_spent: number
  invite_code: string
  invite_count: number
  inviter_id: string
  last_checkin_date: string
  consecutive_checkin_days: number
}

export interface AdminStatistics {
  total_users: number
  active_users: number
  total_generated: number
  total_revenue: number
  today_users: number
  today_generated: number
  today_revenue: number
}

