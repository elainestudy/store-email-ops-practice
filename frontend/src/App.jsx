import { useEffect, useState } from "react";
import { api } from "./api";

const initialForm = {
  name: "",
  subject: "",
  body: "",
  store_id: "",
  recipientsText: "alex@example.com,Alex\njamie@example.com,Jamie"
};

function parseRecipients(recipientsText) {
  return recipientsText
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [email, first_name] = line.split(",").map((part) => part.trim());
      return { email, first_name };
    });
}

function App() {
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState(null);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [recipients, setRecipients] = useState([]);
  const [attempts, setAttempts] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadCampaigns() {
    const result = await api.listCampaigns();
    setCampaigns(result);
    if (!selectedCampaignId && result.length > 0) {
      setSelectedCampaignId(result[0].id);
    }
  }

  async function loadCampaignDetail(campaignId) {
    if (!campaignId) {
      return;
    }

    const [campaign, recipientList, deliveryAttempts, logs] = await Promise.all([
      api.getCampaign(campaignId),
      api.listRecipients(campaignId),
      api.listDeliveryAttempts(campaignId),
      api.listAuditLogs(campaignId)
    ]);

    setSelectedCampaign(campaign);
    setRecipients(recipientList);
    setAttempts(deliveryAttempts);
    setAuditLogs(logs);
  }

  useEffect(() => {
    loadCampaigns().catch((loadError) => setError(loadError.message));
  }, []);

  useEffect(() => {
    loadCampaignDetail(selectedCampaignId).catch((loadError) => setError(loadError.message));
  }, [selectedCampaignId]);

  async function handleCreateCampaign(event) {
    event.preventDefault();
    setError("");
    setInfo("");
    setIsSubmitting(true);

    try {
      const payload = {
        name: form.name,
        subject: form.subject,
        body: form.body,
        store_id: form.store_id,
        recipients: parseRecipients(form.recipientsText)
      };
      const created = await api.createCampaign(payload);
      setInfo("Campaign created.");
      setForm(initialForm);
      await loadCampaigns();
      setSelectedCampaignId(created.id);
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSendCampaign(campaignId) {
    setError("");
    setInfo("");

    try {
      const result = await api.sendCampaign(campaignId);
      setInfo(result.message);
      await loadCampaigns();
      await loadCampaignDetail(campaignId);
    } catch (sendError) {
      setError(sendError.message);
    }
  }

  return (
    <div className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Store Email Operations</p>
          <h1>Internal campaigns with async delivery visibility.</h1>
          <p className="hero-copy">
            Create a store campaign, queue it for asynchronous processing, and inspect
            recipients, delivery attempts, and audit logs in one place.
          </p>
        </div>
        <div className="hero-badge">
          <span>Flask API</span>
          <span>Async Queue</span>
          <span>Audit Trail</span>
        </div>
      </header>

      {error ? <div className="banner error">{error}</div> : null}
      {info ? <div className="banner info">{info}</div> : null}

      <main className="layout">
        <section className="panel form-panel">
          <div className="panel-header">
            <h2>Create Campaign</h2>
            <p>Use one recipient per line in the format `email,first_name`.</p>
          </div>

          <form onSubmit={handleCreateCampaign} className="campaign-form">
            <label>
              Campaign Name
              <input
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                placeholder="Spring Member Event"
              />
            </label>

            <label>
              Subject
              <input
                value={form.subject}
                onChange={(event) => setForm({ ...form, subject: event.target.value })}
                placeholder="New arrivals for members"
              />
            </label>

            <label>
              Store ID
              <input
                value={form.store_id}
                onChange={(event) => setForm({ ...form, store_id: event.target.value })}
                placeholder="store-101"
              />
            </label>

            <label>
              Email Body
              <textarea
                rows="5"
                value={form.body}
                onChange={(event) => setForm({ ...form, body: event.target.value })}
                placeholder="Join us this weekend for a new product preview."
              />
            </label>

            <label>
              Recipients
              <textarea
                rows="6"
                value={form.recipientsText}
                onChange={(event) => setForm({ ...form, recipientsText: event.target.value })}
              />
            </label>

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create Campaign"}
            </button>
          </form>
        </section>

        <section className="panel list-panel">
          <div className="panel-header">
            <h2>Campaigns</h2>
            <p>Operational view for store and support teams.</p>
          </div>

          <div className="campaign-list">
            {campaigns.map((campaign) => (
              <button
                key={campaign.id}
                className={campaign.id === selectedCampaignId ? "campaign-card active" : "campaign-card"}
                onClick={() => setSelectedCampaignId(campaign.id)}
              >
                <div className="campaign-card-top">
                  <strong>{campaign.name}</strong>
                  <span className={`status-chip ${campaign.status}`}>{campaign.status}</span>
                </div>
                <span>{campaign.subject}</span>
                <small>{campaign.store_id}</small>
              </button>
            ))}
          </div>
        </section>

        <section className="panel detail-panel">
          <div className="panel-header">
            <h2>Delivery Detail</h2>
            <p>Inspect recipients, attempts, and audit events.</p>
          </div>

          {selectedCampaign ? (
            <>
              <div className="detail-card">
                <div className="detail-top">
                  <div>
                    <h3>{selectedCampaign.name}</h3>
                    <p>{selectedCampaign.subject}</p>
                  </div>
                  <button onClick={() => handleSendCampaign(selectedCampaign.id)}>Queue Send</button>
                </div>
                <p className="detail-meta">Store: {selectedCampaign.store_id}</p>
              </div>

              <div className="detail-columns">
                <div>
                  <h4>Recipients</h4>
                  <ul className="detail-list">
                    {recipients.map((recipient) => (
                      <li key={recipient.id}>
                        <span>{recipient.first_name}</span>
                        <small>{recipient.email}</small>
                        <strong>{recipient.status}</strong>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4>Delivery Attempts</h4>
                  <ul className="detail-list">
                    {attempts.map((attempt) => (
                      <li key={attempt.id}>
                        <span>{attempt.status}</span>
                        <small>{attempt.provider_message}</small>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div>
                <h4>Audit Trail</h4>
                <ul className="detail-list audit-list">
                  {auditLogs.map((log) => (
                    <li key={log.id}>
                      <span>{log.event_type}</span>
                      <small>{log.message}</small>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          ) : (
            <p className="empty-state">Choose a campaign to inspect delivery details.</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
