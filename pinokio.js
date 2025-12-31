module.exports = {
  version: "2.0",
  title: "JarvisCore",
  description: "AI Assistant with local LLMs, Voice Control & Holographic UI",
  icon: "icon.png",
  menu: async (kernel, info) => {
    // Robuste Prüfung: Pinokio 2.0 nutzt info.running / info.installed
    const running = info.running;
    const installed = info.installed;
    const locals = kernel.script.local(__dirname, "start.json") || {};
    // Port konsolidiert auf 5050 (Backend + Pinokio)
    const url = locals.url || "http://localhost:5050";

    if (!installed) {
      return [
        {
          icon: "fa-solid fa-download",
          text: "Install",
          href: "install.json"
        }
      ];
    }

    if (running) {
      return [
        {
          icon: "fa-solid fa-globe",
          text: "Web UI",
          href: url
        },
        {
          icon: "fa-solid fa-terminal",
          text: "Terminal",
          href: "start.json?terminal=true"
        },
        {
          icon: "fa-solid fa-stop",
          text: "Stop",
          href: "stop.json"
        }
      ];
    }

    return [
      {
        icon: "fa-solid fa-power-off",
        text: "Start",
        href: "start.json"
      },
      {
        icon: "fa-solid fa-rotate",
        text: "Update",
        href: "update.json"
      },
      {
        icon: "fa-solid fa-trash",
        text: "Uninstall",
        href: "uninstall.json"
      }
    ];
  }
};
