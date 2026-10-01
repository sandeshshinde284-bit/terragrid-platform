<template>
  <div class="form-field">
    <label v-if="label" :for="fieldId" class="form-label">
      {{ label }}
      <span v-if="required" class="required">*</span>
    </label>
    <input
      :id="fieldId"
      v-bind="$attrs"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      class="form-input"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      @blur="$emit('blur')"
    />
    <small v-if="error" class="form-error">{{ error }}</small>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FormFieldProps } from '@/types'

withDefaults(
  defineProps<{
    modelValue: string
    type?: string
    label?: string
    placeholder?: string
    error?: string
    required?: boolean
    disabled?: boolean
  }>(),
  {
    type: 'text',
    required: false,
    disabled: false,
  }
)

defineEmits<{
  'update:modelValue': [value: string]
  blur: []
}>()

const fieldId = computed(() => `field-${Date.now()}`)
</script>

<style scoped>
.form-field {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
}

.form-label {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 6px;
  color: #333;
}

.required {
  color: #e74c3c;
}

.form-input {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.3s;
  font-family: inherit;
}

.form-input:focus {
  outline: none;
  border-color: #ff6b6b;
  box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.1);
}

.form-input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.form-error {
  color: #e74c3c;
  font-size: 12px;
  margin-top: 4px;
}
</style>