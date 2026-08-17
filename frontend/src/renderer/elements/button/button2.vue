<style scoped>
  button {
    font-family: Arial, Helvetica, sans-serif;
    font-weight: bold;
    color: white;
    background-color: #1f2937;
    padding: 1em 2em;
    border: none;
    border-radius: .6rem;
    position: relative;
    cursor: pointer;
    overflow: hidden;
  }

  button span:not(:nth-child(6)) {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    height: 34px;
    width: 34px;
    background-color: #22d3ee;
    border-radius: 50%;
    opacity: 0;
    transition: opacity .35s ease, transform .6s ease;
  }

  button span:nth-child(6) {
    position: relative;
  }
  
  button span.text {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  button span:nth-child(1) {
    transform: translate(-3.3em, -4em);
  }

  button span:nth-child(2) {
    transform: translate(-6em, 1.3em);
  }

  button span:nth-child(3) {
    transform: translate(-.2em, 1.8em);
  }

  button span:nth-child(4) {
    transform: translate(3.5em, 1.4em);
  }

  button span:nth-child(5) {
    transform: translate(3.5em, -3.8em);
  }

  button:hover span:not(:nth-child(6)) {
    transform: translate(-50%, -50%) scale(7);
    opacity: 1;
    transition: opacity .4s ease, transform .9s ease;
  }

  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  button:disabled:hover span:not(:nth-child(6)) {
    transform: translate(-50%, -50%);
    transition: none;
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
    @click="handleClick"
  >
    <span class="circle1"></span>
    <span class="circle2"></span>
    <span class="circle3"></span>
    <span class="circle4"></span>
    <span class="circle5"></span>
    <span class="text"><slot /></span>
  </button>
</template>
