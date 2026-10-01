<template>
  <button
    :class="['btn', `btn-${variant}`, `btn-${size}`, { 'btn-loading': loading }]"
    :disabled="disabled || loading"
    @click="$emit('click')"
  >
    <span v-if="loading" class="spinner"></span>
    <slot></slot>
  </button>
</template>

<script setup lang="ts">
import type { ButtonProps } from '@/types'

withDefaults(
  defineProps<{
    variant?: ButtonProps['variant']
    size?: ButtonProps['size']
    disabled?: boolean
    loading?: boolean
  }>(),
  {
    variant: 'primary',
    size: 'md',
    disabled: false,
    loading: false,
  }
)

defineEmits<{
  click: []
}>()
</script>

<style scoped>
.btn {
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: inherit;
}

.btn-primary {
  background-color: #ff6b6b;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #e55555;
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
}

.btn-secondary {
  background-color: #1e3a5f;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #162a45;
}

.btn-danger {
  background-color: #e74c3c;
  color: white;
}

.btn-ghost {
  background-color: transparent;
  border: 2px solid #ddd;
  color: #333;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 12px;
}

.btn-md {
  padding: 10px 16px;
  font-size: 14px;
}

.btn-lg {
  padding: 14px 24px;
  font-size: 16px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>