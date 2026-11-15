<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{ (e: 'select', emoji: string): void }>()

const visible = ref(false)

const RECENT_KEY = 'emoji_recent'
const MAX_RECENT = 24

// Commonly used emoji organized by category
const EMOJI_GROUPS = [
  {
    name: '常用',
    emojis: '😀😂🤣😊😍🤩😘😜🤔😏😌😴🤗🤭🫣🫠😵💀👻🤖🎉💯🔥❤️👍👎🙏👋🤝💪',
  },
  {
    name: '表情',
    emojis: '😀😃😄😁😆😅🤣😂🙂🙃😉😊😇🥰😍🤩😘😗☺️😚😋😛😜🤪😝🤑🤗🤭🫢🫣🤫🤔🤐🤨😐😑😶😏😒🙄😬🤥😌😔😪🤤😴😷🤒🤕🤢🤮🤧🥵🥶🥴😵🤯🤠🥳🥸😎🤓🧐😕😟🙁😮😯😲😳🥺😦😧😨😰😥😢😭😱😖😣😞😓😩😫🥱😤😡😠🤬',
  },
  {
    name: '手势',
    emojis: '👋🤚🖐✋🖖👌🤌🤏✌️🤞🤟🤘🤙👈👉👆🖕👇☝️👍👎✊👊🤛🤜👏🙌👐🤲🤝🙏',
  },
  {
    name: '动物',
    emojis: '🐶🐱🐭🐹🐰🦊🐻🐼🐻‍❄️🐨🐯🦁🐮🐷🐽🐸🐵🙈🙉🙊🐒🐔🐧🐦🐤🐣🐥🦆🦅🦉🦇🐺🐗🐴🦄🐝🪱🐛🦋🐌🐞🐜🪰🪲🪳🦟🦗🕷🦂🐢🐍🦎🦖🦕🐙🦑🦐🦞🦀🐡🐠🐟🐬🐳🐋🦈🦭🐊🐅🐆🦓🦍🦧🐘🦛🦏🐪🐫🦒🦘🦬🐃🐂🐄🐎🐖🐏🐑🦙🐐🦌🐕🐩🦮🐕‍🦺🐈🐈‍⬛🪶🐓🦃🦤🦚🦜🦢🦩🕊',
  },
  {
    name: '物品',
    emojis: '💻🖥⌨️🖱🖨📱☎️📞📟📠🔋🔌💡🔦🕯🧯🛢💸💵💴💶💷🪙💰💳💎⚖️🔧🔨⚒🛠⛏🔩⚙️🧱⛓🧲🔫💣🧨🪓🔪🗡⚔️🛡🚬⚰️⚱️🏺🔮📿🧿💈⚗️🔭🔬🕳🩻🩹🩺💊💉🩸🧬🦠🧫🧪🌡🧹🧺🧻🚽🚰🚿🛁🧼🪥🪒🧽🪣🧴🛎🔑🗝🚪🪑🛏🛋🪟🪞🖼🛍🛒🎁🎈🎏🎀🪄🪅🎊🎉🎎🏮🎐🧧✉️📩📨📧💌📥📤📦🏷📪📫📬📭📮📯📜📃📄📑🧾📊📈📉🗒🗓📆📅🗑📇🗃🗳🗄📋📁📂🗂🗞📰📓📔📒📕📗📘📙📚📖🔖🧷🔗📎🖇📐📏🧮📌📍✂️🖊🖋✒️🖌🖍📝✏️🔍🔎🔏🔐🔒🔓',
  },
  {
    name: '符号',
    emojis: '❤️🧡💛💚💙💜🤎🖤🤍♥️💘💝💖💗💓💞💕❣️💔❤️‍🔥❤️‍🩹💟💌💤💢💦💨🕳💣💬🗨🗯💭🫧♨️💫🕐🕑🕒🕓🕔🕕🕖🕗🕘🕙🕚🕛🔄🔃🔙🔚🔛🔜🔝🛐⚛️🕉✡️☸️☯️✝️☦️☪️☮️🕎🔯♈♉♊♋♌♍♎♏♐♑♒♓⛎🔀🔁🔂▶️⏩⏭⏯◀️⏪⏮🔼⏫🔽⏬⏸⏹⏺⏏🎦🔅🔆📶📳📴♀️♂️⚧✖️➕➖➗♾‼️⁉️❓❔❕❗〰️💱💲⚕️♻️⚜️🔱📛🔰⭕✅☑️✔️❌❎➰➿〽️✳️✴️❇️©️®️™️',
  },
]

function getRecent(): string[] {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]')
  } catch { return [] }
}

function addRecent(emoji: string) {
  const recent = getRecent().filter(e => e !== emoji)
  recent.unshift(emoji)
  localStorage.setItem(RECENT_KEY, JSON.stringify(recent.slice(0, MAX_RECENT)))
}

function select(emoji: string) {
  addRecent(emoji)
  emit('select', emoji)
}

const recent = getRecent()

// Close on click outside
function onBackdrop(e: MouseEvent) {
  if ((e.target as HTMLElement).classList.contains('emoji-backdrop')) {
    visible.value = false
  }
}

function close() { visible.value = false }
defineExpose({ visible, close })
</script>

<template>
  <div class="emoji-trigger" @click="visible = !visible">
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" class="emoji-icon">
      <circle cx="12" cy="12" r="10"/>
      <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
      <line x1="9" y1="9" x2="9.01" y2="9"/>
      <line x1="15" y1="9" x2="15.01" y2="9"/>
    </svg>
  </div>

  <Teleport to="body">
    <div v-if="visible" class="emoji-backdrop" @click="onBackdrop">
      <div class="emoji-panel">
        <div class="emoji-panel-header">
          <span class="emoji-tabs-label">选择表情</span>
          <span class="emoji-close" @click="visible = false">✕</span>
        </div>
        <div class="emoji-scroll">
          <div v-if="recent.length > 0" class="emoji-group">
            <div class="emoji-group-label">最近使用</div>
            <div class="emoji-grid">
              <span v-for="e in recent" :key="'r'+e" class="emoji-cell" @click="select(e)">{{ e }}</span>
            </div>
          </div>
          <div v-for="group in EMOJI_GROUPS" :key="group.name" class="emoji-group">
            <div class="emoji-group-label">{{ group.name }}</div>
            <div class="emoji-grid">
              <span v-for="(e, i) in [...group.emojis]" :key="group.name + i" class="emoji-cell" @click="select(e)">{{ e }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.emoji-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 6px;
  cursor: pointer;
  color: #999;
  transition: all 0.15s;
}
.emoji-trigger:hover { background: #e8e8e8; color: #666; }

.emoji-icon { flex-shrink: 0; }

.emoji-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.emoji-panel {
  background: #fff;
  border-radius: 12px 12px 0 0;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.12);
  width: 100%;
  max-width: 420px;
  max-height: 360px;
  display: flex;
  flex-direction: column;
  margin-bottom: 8px;
}

.emoji-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid #eee;
}
.emoji-tabs-label { font-size: 14px; font-weight: 600; color: #333; }
.emoji-close { cursor: pointer; color: #999; font-size: 16px; padding: 4px; }

.emoji-scroll { overflow-y: auto; flex: 1; padding: 8px 12px 16px; }

.emoji-group { margin-bottom: 12px; }
.emoji-group-label { font-size: 12px; color: #999; margin-bottom: 6px; padding-left: 2px; }

.emoji-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
}

.emoji-cell {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.1s;
}
.emoji-cell:hover { background: #f0f0f0; }
</style>