<template>
  <div class="causal-chain-explanation">
    <div class="chain-title" style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px; border-bottom: 2px solid #1e293b; padding-bottom: 16px;">
      <span class="icon" style="font-size: 20px;">🔗</span>
      <h3 style="margin: 0; font-size: 16px; font-weight: 800; color: #f8fafc; letter-spacing: 0.08em; text-transform: uppercase;">CAUSAL CHAIN ANALYSIS</h3>
      <span class="subtitle" style="margin-left: auto; color: #94a3b8; font-size: 13px; font-style: italic;">Why Is This Disaster Happening?</span>
    </div>

    <!-- TRIGGER -->
    <div class="chain-step trigger" style="display: flex; gap: 16px; margin-bottom: 8px; padding: 16px; border-left: 4px solid #ef4444; border-radius: 8px; background: rgba(15, 23, 42, 0.6);">
      <div class="step-badge" style="display: inline-block; font-weight: 800; font-size: 11px; padding: 6px 10px; border-radius: 4px; white-space: nowrap; flex-shrink: 0; align-self: flex-start; color: #ef4444; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3);">🔴 TRIGGER</div>
      <div class="step-content" style="flex: 1;">
        <h4 style="margin: 0 0 8px 0; color: #cbd5e1; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">What Started This?</h4>
        <p style="margin: 0; color: #e2e8f0; font-size: 15px; line-height: 1.6; max-width: 85ch;">{{ causalData.trigger_event }}</p>
      </div>
    </div>

    <!-- Arrow Down -->
    <div class="chain-arrow" style="text-align: center; color: #64748b; font-size: 20px; padding: 8px 0; font-weight: bold;">↓</div>

    <!-- INFRASTRUCTURE FACTORS -->
    <div class="chain-step infrastructure" style="display: flex; gap: 16px; margin-bottom: 8px; padding: 16px; border-left: 4px solid #f97316; border-radius: 8px; background: rgba(15, 23, 42, 0.6);">
      <div class="step-badge" style="display: inline-block; font-weight: 800; font-size: 11px; padding: 6px 10px; border-radius: 4px; white-space: nowrap; flex-shrink: 0; align-self: flex-start; color: #f97316; background: rgba(249, 115, 22, 0.15); border: 1px solid rgba(249, 115, 22, 0.3);">🟠 INFRASTRUCTURE STRESS</div>
      <div class="step-content" style="flex: 1;">
        <h4 style="margin: 0 0 8px 0; color: #cbd5e1; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">How Systems Are Overwhelmed</h4>
        <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; color: #e2e8f0; font-size: 15px; line-height: 1.6; max-width: 85ch;">
          <li v-for="(factor, idx) in causalData.infrastructure_factors" :key="idx" style="display: flex; gap: 8px;">
            <span style="font-weight: bold; color: #f97316;">•</span> {{ factor }}
          </li>
        </ul>
      </div>
    </div>

    <!-- Arrow Down -->
    <div class="chain-arrow" style="text-align: center; color: #64748b; font-size: 20px; padding: 8px 0; font-weight: bold;">↓</div>

    <!-- PREDICTED RESULT -->
    <div class="chain-step result" style="display: flex; gap: 16px; margin-bottom: 8px; padding: 16px; border-left: 4px solid #eab308; border-radius: 8px; background: rgba(15, 23, 42, 0.6);">
      <div class="step-badge" style="display: inline-block; font-weight: 800; font-size: 11px; padding: 6px 10px; border-radius: 4px; white-space: nowrap; flex-shrink: 0; align-self: flex-start; color: #eab308; background: rgba(234, 179, 8, 0.15); border: 1px solid rgba(234, 179, 8, 0.3);">🟡 PREDICTED RESULT</div>
      <div class="step-content" style="flex: 1;">
        <h4 style="margin: 0 0 8px 0; color: #cbd5e1; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">What Happens Next</h4>
        <p style="margin: 0; color: #e2e8f0; font-size: 15px; line-height: 1.6; max-width: 85ch;">{{ causalData.predicted_outcome }}</p>
      </div>
    </div>

    <!-- Arrow Down -->
    <div class="chain-arrow" style="text-align: center; color: #64748b; font-size: 20px; padding: 8px 0; font-weight: bold;">↓</div>

    <!-- HISTORICAL PRECEDENT -->
    <div class="chain-step history" style="display: flex; gap: 16px; margin-bottom: 8px; padding: 16px; border-left: 4px solid #38bdf8; border-radius: 8px; background: rgba(15, 23, 42, 0.6);">
      <div class="step-badge" style="display: inline-block; font-weight: 800; font-size: 11px; padding: 6px 10px; border-radius: 4px; white-space: nowrap; flex-shrink: 0; align-self: flex-start; color: #38bdf8; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3);">📚 HISTORICAL PRECEDENT</div>
      <div class="step-content" style="flex: 1;">
        <h4 style="margin: 0 0 8px 0; color: #cbd5e1; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Similar Past Events</h4>
        <p style="margin: 0; color: #e2e8f0; font-size: 15px; line-height: 1.6; max-width: 85ch;">{{ causalData.historical_reference }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  causalData: {
    trigger_event: string
    infrastructure_factors: string[]
    predicted_outcome: string
    historical_reference: string
  }
}>()
</script>

<style scoped>
.causal-chain-explanation {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  padding: 24px;
  margin-top: 18px;
  margin-bottom: 18px;
}

@media (max-width: 768px) {
  .causal-chain-explanation { padding: 16px; }
  .chain-title { flex-direction: column; align-items: flex-start; }
  .chain-title .subtitle { margin-left: 0 !important; margin-top: 8px; }
  .chain-step { flex-direction: column; }
  .step-badge { align-self: flex-start; margin-bottom: 8px; }
}
</style>