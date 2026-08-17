<style scoped>
  button {
    --button_radius: 0.75em;
    --button_color: #e8e8e8;
    --button_outline_color: #000000;
    --button_font_size: 17px;
    --button_padding: 0.75em 1.5em;
    font-size: var(--button_font_size);
    font-weight: bold;
    border: none;
    cursor: pointer;
    border-radius: var(--button_radius);
    background: var(--button_outline_color);
  }

  .button_top {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    box-sizing: border-box;
    border: 2px solid var(--button_outline_color);
    border-radius: var(--button_radius);
    padding: var(--button_padding);
    background: var(--button_color);
    color: var(--button_outline_color);
    transform: translateY(-0.2em);
    transition: transform 0.1s ease;
  }

  button:hover .button_top {
    transform: translateY(-0.33em);
  }

  button:active .button_top {
    transform: translateY(0);
  }

  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  button:disabled .button_top {
    transform: translateY(0);
  }

  button.size-small {
    --button_font_size: 14px;
    --button_padding: 0.45em 1.1em;
  }

  button.size-icon {
    --button_font_size: 14px;
    --button_padding: 0;
  }

  button.size-icon .button_top {
    width: 40px;
    height: 40px;
    padding: 0;
  }
</style>

<script setup>
const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  },
  nativeType: {
    type: String,
    default: 'button'
  },
  ariaLabel: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: ''
  },
  size: {
    type: String,
    default: 'normal'
  }
})

const emit = defineEmits(['click'])

const handleClick = (e) => {
  emit('click', e)
}
</script>

<template>
  <button
    :type="props.nativeType"
    :disabled="props.disabled"
    :aria-label="props.ariaLabel || undefined"
    :title="props.title || undefined"
    :class="`size-${props.size}`"
    @click="handleClick"
  >
    <span class="button_top">
      <slot />
    </span>
  </button>
</template>
