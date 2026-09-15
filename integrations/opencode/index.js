import { readFile } from "node:fs/promises"
import { fileURLToPath } from "node:url"

const skill = {
  id: "prism-callee-lifecycle",
  name: "Prism Callee Lifecycle",
  description: "Run complete Prism Story or Epic workflows through Callee agents.",
  url: new URL(
    "../../plugins/prism-callee/prefixed-skills/prism-callee-lifecycle/SKILL.md",
    import.meta.url,
  ),
}

function body(markdown) {
  return markdown.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, "")
}

export default {
  id: "prism-callee",
  async setup(ctx) {
    const content = body(await readFile(skill.url, "utf8"))

    await ctx.skill.transform((editor) => {
      editor.add({
        id: skill.id,
        name: skill.name,
        description: skill.description,
        location: fileURLToPath(skill.url),
        content,
      })
    })
  },
}
