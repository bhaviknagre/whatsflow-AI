export type Conversation = {
  id: string;
  organization_id: string;
  whatsapp_connection_id: string;
  customer_phone_number: string;
  unread_count: number;
  created_at: string;
  updated_at: string;
};

export type Message = {
  id: string;
  conversation_id: string;
  whatsapp_message_id: string | null;
  direction: string;
  message_type: string;
  text: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type SendMessageRequest = {
  text: string;
};

export type WhatsAppConnectionSummary = {
  id: string;
  waba_id: string;
  phone_number_id: string;
  display_phone_number: string | null;
  verified_name: string | null;
  is_active: boolean;
};

export type ConversationListItem = {
  id: string;
  whatsapp_connection_id: string;
  customer_phone_number: string;
  last_message: Message | null;
  unread_count: number;
  created_at: string;
  updated_at: string;
};

export type ConversationResponse = {
  id: string;
  whatsapp_connection_id: string;
  customer_phone_number: string;
  unread_count: number;
  created_at: string;
  updated_at: string;
  messages: Message[];
  whatsapp_connection: WhatsAppConnectionSummary;
};

export type MessageTemplateSummary = {
  name: string;
  language: string;
  category: string;
  body_text: string | null;
  placeholder_count: number;
};

export type StartConversationRequest = {
  customer_phone_number: string;
  template_name: string;
  language_code: string;
  parameters: string[];
};
