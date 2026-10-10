<template>
  <div class="alerts-tab">
    <div class="tab-intro">
      <div>
        <h2>Alert Management</h2>
        <p>Multi-channel emergency broadcast analytics and public notification dispatch tracking.</p>
      </div>
    </div>

    <!-- Live Email Dispatch Engine (Phase 1) -->
    <article class="glass-panel" style="margin-bottom: 20px; padding: 20px;">
      <div class="panel-heading" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
          <span class="section-kicker" style="color: #94a3b8; font-size: 15px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; display: block;">AUTOMATED DISPATCH</span>
          <h3 style="margin: 0; font-size: 18px; color: #f8fafc;">Commander Alert Engine</h3>
        </div>
        <span class="ai-chip live" style="font-size: 16px; font-weight: 800; color: #34d399; background: rgba(52, 211, 153, 0.15); border: 1px solid rgba(52, 211, 153, 0.3); padding: 4px 8px; border-radius: 4px;">LIVE</span>
      </div>

      <div class="dispatch-log">
        <div class="log-entry" style="display: flex; align-items: flex-start; gap: 16px; padding-bottom: 16px; border-bottom: 1px solid #1e293b;">
          <div class="log-icon" style="font-size: 24px;">📧</div>
          <div class="log-content" style="flex: 1;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
              <strong style="color: #f8fafc; font-size: 16px;">Tactical HTML Brief Dispatched</strong>
              <span style="color: #4ade80; font-weight: 700; font-size: 16px;">DELIVERED</span>
            </div>
            <p style="margin: 0 0 8px 0; color: #cbd5e1; font-size: 15px;">Recipient: <strong style="color: #38bdf8; font-family: ui-monospace, monospace; font-weight: normal;">sandeshshinde284@gmail.com</strong></p>
            <div style="display: flex; gap: 16px; color: #64748b; font-size: 16px;">
              <span>Gateway: Resend API</span>
              <span>Trigger: Critical Threat Threshold Breached</span>
            </div>
          </div>
        </div>
      </div>
    </article>

    <!-- Multi-Channel Expansion (Phase 2) -->
    <div class="content-grid two-columns" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px;">
      
      <!-- SMS / WhatsApp -->
      <article class="glass-panel" style="padding: 20px; background: rgba(15, 23, 42, 0.4); border: 1px dashed rgba(148, 163, 184, 0.2);">
        <div class="panel-heading" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <div>
            <h3 style="margin: 0; font-size: 16px; color: #94a3b8;">Mass SMS / WhatsApp Broadcast</h3>
          </div>
          <span style="font-size: 15px; font-weight: 800; color: #94a3b8; background: rgba(148, 163, 184, 0.1); padding: 4px 8px; border-radius: 4px;">PHASE 2</span>
        </div>
        <p style="color: #64748b; font-size: 15px; margin: 0;">Integration with Twilio Programmable SMS and Meta WhatsApp Business API for civilian reverse-911 evacuation targeting.</p>
      </article>

      <!-- Emergency Radio -->
      <article class="glass-panel" style="padding: 20px; background: rgba(15, 23, 42, 0.4); border: 1px dashed rgba(148, 163, 184, 0.2);">
        <div class="panel-heading" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <div>
            <h3 style="margin: 0; font-size: 16px; color: #94a3b8;">EAS / NOAA Radio Integration</h3>
          </div>
          <span style="font-size: 15px; font-weight: 800; color: #94a3b8; background: rgba(148, 163, 184, 0.1); padding: 4px 8px; border-radius: 4px;">PHASE 2</span>
        </div>
        <p style="color: #64748b; font-size: 15px; margin: 0;">Automated text-to-speech injection into the National Emergency Alert System and localized FM/AM broadcast towers.</p>
      </article>

    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  isBackendMockModeEnabled: boolean
  detail: any
}>()

defineEmits(['open-alerts'])
</script>

<style scoped>
.glass-panel {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  padding: 20px;
}
.phase2-center-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 20px;
}
.phase2-card {
  max-width: 520px;
  width: 100%;
  padding: 40px 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(15, 23, 42, 0.75);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 16px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}
.phase2-icon {
  font-size: 48px;
  margin-bottom: 16px;
  filter: drop-shadow(0 0 12px rgba(14, 165, 233, 0.4));
}
.phase2-tag {
  display: inline-block;
  font-size: 18px;
  font-weight: 800;
  padding: 5px 14px;
  border-radius: 999px;
  background: rgba(14, 165, 233, 0.2);
  color: #38bdf8;
  border: 1px solid rgba(14, 165, 233, 0.4);
  letter-spacing: 1px;
  margin-bottom: 16px;
}
.response-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}
.primary-button {
  background: #0284c7;
  border: 1px solid #0284c7;
  color: #ffffff;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-weight: 700;
}
.primary-button:hover {
  background: #0369a1;
  border-color: #0369a1;
}

@media (max-width: 768px) {
  .glass-panel { padding: 16px !important; }
  .panel-heading { flex-direction: column; align-items: flex-start; gap: 8px; margin-bottom: 16px !important; }
  h2, h3 { font-size: 16px !important; }
  .ai-resource-table th, .ai-resource-table td { padding: 8px 6px !important; font-size: 15px !important; white-space: nowrap; }
  .resource-matrix-table-wrapper { padding-bottom: 12px; margin-bottom: -12px; }
  .priority-tag { font-size: 16px !important; padding: 2px 6px !important; }
  .cascade-header { flex-direction: column; align-items: flex-start !important; gap: 8px; }
  .demo-stat-row { flex-direction: column; gap: 12px !important; }
  .route-highlight { flex-direction: column; align-items: flex-start !important; }
  .source-cards { grid-template-columns: 1fr !important; }
  .freshness-list div { flex-direction: column; gap: 4px !important; margin-bottom: 8px; }
  .freshness-list strong { text-align: left !important; }
  .insights-grid { grid-template-columns: 1fr !important; }
  .action-item { flex-direction: column; gap: 8px !important; }
}

</style>