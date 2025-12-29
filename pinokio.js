const path = require('path')
module.exports = {
  version: "1.2",
  title: "JarvisCore",
  description: "AI Assistant with local LLMs, Voice Control & Holographic UI",
  icon: "icon.png",
  menu: async (kernel) => {
    let installed = await kernel.exists(__dirname, "venv")
    if (installed) {
      let session = await kernel.require(__dirname, "session.json")
      let running = session && session.running
      if (running) {
        return [{
          icon: "fa-solid fa-spin fa-circle-notch",
          text: "Running",
          href: "start.json"
        }, {
          icon: "fa-solid fa-terminal",
          text: "Terminal",
          href: "start.json",
          params: { fullscreen: true }
        }, {
          icon: "fa-solid fa-stop",
          text: "Stop",
          href: "stop.json"
        }]
      } else {
        return [{
          icon: "fa-solid fa-power-off",
          text: "Start",
          href: "start.json"
        }, {
          icon: "fa-solid fa-wrench",
          text: "Update",
          href: "update.json"
        }, {
          icon: "fa-solid fa-trash",
          text: "Uninstall",
          href: "uninstall.json"
        }]
      }
    } else {
      return [{
        icon: "fa-solid fa-download",
        text: "Install",
        href: "install.json"
      }]
    }
  }
}