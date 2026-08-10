export type CampaignRecipient = {
  id: string;
  campaign_id: string;
  contact_id: string | null;
  phone_number: string;
  parameters: string[];
  rendered_text: string | null;
  status: string;
  whatsapp_message_id: string | null;
  error_code: string | null;
  error_message: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  read_at: string | null;
  failed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Campaign = {
  id: string;
  organization_id: string;
  whatsapp_connection_id: string;
  name: string;
  template_name: string;
  language_code: string;
  status: string;
  scheduled_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  total_recipients: number;
  sent_count: number;
  delivered_count: number;
  read_count: number;
  failed_count: number;
  created_at: string;
  updated_at: string;
};

export type CampaignDetail = Campaign & {
  recipients: CampaignRecipient[];
};

export type CampaignRecipientInput = {
  phone_number: string;
  contact_id?: string | null;
  parameters: string[];
};

export type CreateCampaignRequest = {
  name: string;
  template_name: string;
  language_code: string;
  recipients: CampaignRecipientInput[];
  scheduled_at?: string | null;
};
