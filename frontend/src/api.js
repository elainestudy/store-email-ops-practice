const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    const message = body?.error || "Request failed";
    throw new Error(message);
  }

  return body;
}

export const api = {
  listCampaigns() {
    return request("/campaigns");
  },
  createCampaign(payload) {
    return request("/campaigns", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  sendCampaign(campaignId) {
    return request(`/campaigns/${campaignId}/send`, {
      method: "POST"
    });
  },
  getCampaign(campaignId) {
    return request(`/campaigns/${campaignId}`);
  },
  listRecipients(campaignId) {
    return request(`/campaigns/${campaignId}/recipients`);
  },
  listDeliveryAttempts(campaignId) {
    return request(`/campaigns/${campaignId}/delivery-attempts`);
  },
  listAuditLogs(campaignId) {
    return request(`/campaigns/${campaignId}/audit-logs`);
  }
};
