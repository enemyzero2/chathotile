declare module 'vue3-emoji-picker' {
  import { DefineComponent } from 'vue'
  
  interface EmojiClickEvent {
    i: string
    n: string[]
    r: string
    t: string
    u: string
  }

  const EmojiPicker: DefineComponent<{}, {}, any>
  
  export default EmojiPicker
  export type { EmojiClickEvent }
} 